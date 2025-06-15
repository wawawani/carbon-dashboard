@app.route("/api/emissions/waste", methods=["GET"])
def waste_emissions_updated():
    filepath = os.path.join(DATA_DIR, "waste.csv")
    if not os.path.exists(filepath):
        return jsonify({"error": "waste.csv 파일이 없습니다."}), 404

    df = pd.read_csv(filepath)

    # 기본값 초기화
    df["탄소배출량"] = 0.0

    # 의료폐기물 - 매립
    mask_med_landfill = (df["종류"] == "의료폐기물") & (df["처리방식"] == "매립")
    df.loc[mask_med_landfill, "탄소배출량"] = (
        df.loc[mask_med_landfill, "MSW"] *
        df.loc[mask_med_landfill, "DOC"] *
        df.loc[mask_med_landfill, "DOCj"] *
        df.loc[mask_med_landfill, "MCF"] *
        df.loc[mask_med_landfill, "F"] *
        (16 / 12) *
        (1 - df.loc[mask_med_landfill, "R"])
    )

    # 의료폐기물 - 소각
    mask_med_inc = (df["종류"] == "의료폐기물") & (df["처리방식"] == "소각")
    df.loc[mask_med_inc, "탄소배출량"] = (
        df.loc[mask_med_inc, "MSW"] *
        df.loc[mask_med_inc, "소각배출계수"]
    )

    # 지정폐기물 (매립)
    mask_des = (df["종류"] == "지정폐기물")
    df.loc[mask_des, "탄소배출량"] = (
        df.loc[mask_des, "MSW"] *
        df.loc[mask_des, "DOC"] *
        df.loc[mask_des, "DOCj"] *
        df.loc[mask_des, "MCF"] *
        df.loc[mask_des, "F"] *
        (16 / 12) *
        (1 - df.loc[mask_des, "R"])
    )

    # 산업폐수
    mask_indus = (df["종류"] == "산업폐수")
    df.loc[mask_indus, "탄소배출량"] = (
        df.loc[mask_indus, "TOW"] *
        df.loc[mask_indus, "EF"] *
        (1 - df.loc[mask_indus, "R"])
    )

    # 날짜별 합산
    result = df.groupby("날짜")["탄소배출량"].sum().reset_index()
    result["탄소배출량"] = result["탄소배출량"].round(4)
    return jsonify(result.to_dict(orient="records"))

@app.route("/api/emissions/water", methods=["GET"])
def water_emissions():
    filepath = os.path.join(DATA_DIR, "water.csv")
    if not os.path.exists(filepath):
        return jsonify({"error": "CSV file not found."}), 404

    df = pd.read_csv(filepath)

    # 탄소배출량 계산
    df["탄소배출량"] = df["총량"] * df["전력원단위"] * df["배출계수"]

    result = df[["날짜", "탄소배출량"]].copy()
    result["탄소배출량"] = result["탄소배출량"].round(2)
    return jsonify(result.to_dict(orient="records"))

@app.route("/api/emissions/electric", methods=["GET"])
def electric_emissions():
    filepath = os.path.join(DATA_DIR, "electric.csv")
    if not os.path.exists(filepath):
        return jsonify({"error": "electric.csv not found."}), 404

    df = pd.read_csv(filepath)

    df["탄소배출량"] = df["총 사용 전력량"] * df["배출계수"]
    result = df[["날짜", "탄소배출량"]].copy()
    result["탄소배출량"] = result["탄소배출량"].round(2)
    return jsonify(result.to_dict(orient="records"))

@app.route("/api/emissions/greenery", methods=["GET"])
def greenery_total_emissions():
    total_absorption = 0.0

    # === 면적 기반 ===
    area_path = os.path.join(DATA_DIR, "greenery_area.csv")
    if os.path.exists(area_path):
        df_area = pd.read_csv(area_path)

        def calc_area(row):
            if row["구분"] == "Land Area":
                return row["면적(m²)"] * row["carbon_uptake"] + row["면적(m²)"] * row["carbon_storage"]
            elif row["구분"] == "Tree Cover":
                return row["면적(m²)"] * row["carbon_storage"]
            return 0

        df_area["흡수량"] = df_area.apply(calc_area, axis=1)
        total_absorption += df_area["흡수량"].sum()

    # === 나무 기반 ===
    tree_path = os.path.join(DATA_DIR, "greenery_tree.csv")
    if os.path.exists(tree_path):
        df_tree = pd.read_csv(tree_path)

        df_tree["단위흡수량"] = (
            df_tree["ΔV"] * df_tree["D"] * df_tree["BEF"] *
            (1 + df_tree["R"]) * df_tree["CF"] * (44 / 12)
        )
        df_tree["총흡수량"] = df_tree["단위흡수량"] * df_tree["개체수"]
        total_absorption += df_tree["총흡수량"].sum()

    return jsonify({
        "총 탄소흡수량(tCO₂)": round(total_absorption, 4)
    })
