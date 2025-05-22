from flask import Flask, jsonify
import pandas as pd
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/emission/vehicle', methods=['GET'])
def vehicle_emission():
    filepath = 'data/vehicle.csv'
    if not os.path.exists(filepath):
        return jsonify({"error": "CSV file not found. Please upload vehicle.csv to data/ folder."}), 404

    df = pd.read_csv(filepath)
    factors = {'gasoline': 2.31, 'diesel': 2.68}
    df['emission'] = df.apply(
        lambda row: row['distance_km'] * factors.get(row['fuel_type'], 0),
        axis=1
    )

    result = df[['date', 'emission']]
    return jsonify(result.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
