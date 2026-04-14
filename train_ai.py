import Orange

print("====================================")
print(" 🧠 AQUAPATH AI: MATH REGRESSION ")
print("====================================\n")

# --- 1. WEATHER REGRESSION ---
# Load the raw CSV
raw_weather = Orange.data.Table("weather_training.csv")

# Explicitly tell Orange that the LAST column is our NUMERIC Target
weather_domain = Orange.data.Domain(
    attributes=raw_weather.domain.attributes[:-1], 
    class_vars=Orange.data.ContinuousVariable(raw_weather.domain.attributes[-1].name)
)
weather_data = Orange.data.Table.from_table(weather_domain, raw_weather)

# Train the Model
lin_reg = Orange.regression.LinearRegressionLearner()
print("Calculating Weather Formula...")
weather_model = lin_reg(weather_data)

# Print the Formula
print("\n[Weather Risk Equation]")
formula_parts = []
for attr, coef in zip(weather_data.domain.attributes, weather_model.coefficients):
    formula_parts.append(f"({round(coef, 4)} * {attr.name})")

intercept = round(weather_model.intercept, 4)
print(f"Risk = {' + '.join(formula_parts)} + ({intercept})")


# --- 2. TRAFFIC REGRESSION ---
# Load the raw CSV
raw_traffic = Orange.data.Table("traffic_training.csv")

# Explicitly tell Orange that the LAST column is our NUMERIC Target
traffic_domain = Orange.data.Domain(
    attributes=raw_traffic.domain.attributes[:-1], 
    class_vars=Orange.data.ContinuousVariable(raw_traffic.domain.attributes[-1].name)
)
traffic_data = Orange.data.Table.from_table(traffic_domain, raw_traffic)

# Train the Model
print("\nCalculating Traffic Formula...")
traffic_model = lin_reg(traffic_data)

# Print the Formula
print("\n[Traffic Risk Equation]")
t_formula = []
for attr, coef in zip(traffic_data.domain.attributes, traffic_model.coefficients):
    t_formula.append(f"({round(coef, 4)} * {attr.name})")

t_intercept = round(traffic_model.intercept, 4)
print(f"Risk = {' + '.join(t_formula)} + ({t_intercept})\n")