import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

df = pd.read_csv("(file path)/cybersecurity synthesized data.csv")

print(df.head())
print(df.info())
print(df.columns)

#converting timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

#extracting time features
df['year'] = df['timestamp'].dt.year
df['month'] = df['timestamp'].dt.month
df['day'] = df['timestamp'].dt.day
df['hour'] = df['timestamp'].dt.hour

#checking duplicates anddropping them
df.duplicated().sum()
df = df.drop_duplicates()

#checking uniques values in categorical columns
for col in ['attack_type','target_system','outcome','industry','location']:
    print(col, df[col].nunique())

print(df['attack_type'].unique())

#aligning attack types
df['attack_type'] = df['attack_type'].str.lower().str.strip()

#droping useless columns
df = df.drop(['attacker_ip', 'target_ip'], axis=1)
print(df.head())

#detecting outliers
sns.boxplot(df['data_compromised_GB'])
plt.show()

#detecting outliers using IQR
Q1 = df['data_compromised_GB'].quantile(0.25)
Q3 = df['data_compromised_GB'].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

print("\n Outlier Bounds:")
print("Lower:", lower, "Upper:", upper)

before = df.shape[0]

df = df[(df['data_compromised_GB'] >= lower) & (df['data_compromised_GB'] <= upper)]

after = df.shape[0]

print("Rows before:", before)
print("Rows after removing outliers:", after)

#checking response and attack duration
invalid_cases = df[df['response_time_min'] > df['attack_duration_min']]
print("\n Cases where response time > attack duration:", invalid_cases.shape[0])
print(invalid_cases.head())

#adding new feature instead of removing rows
df['delayed_response'] = df.apply(
    lambda row: 1 if row['response_time_min'] > row['attack_duration_min'] else 0,
    axis=1
)
print("\nDelayed Response Count:")
print(df['delayed_response'].value_counts())

#creating severity levels
def severity_label(x):
    if x <= 3:
        return 'low'
    elif x <= 6:
        return 'medium'
    else:
        return 'high'

df['severity_label'] = df['attack_severity'].apply(severity_label)
print("\n Severity label created")
print(df[['attack_severity','severity_label']].head())

#checking skewness of data compromised and applying log transformation
df['data_compromised_log'] = np.log1p(df['data_compromised_GB'])
print("\n Log transformation applied on data_compromised_GB")
print(df[['data_compromised_GB', 'data_compromised_log']].head())

#showcasing final shape 
print("\n Final Cleaned Dataset Shape:", df.shape)

#performing feature engineering
df['high_risk'] = df['attack_severity'].apply(lambda x: 1 if x >= 7 else 0)
df['attack_success'] = df['outcome'].apply(lambda x: 1 if x.lower() == 'success' else 0)
df['response_efficiency'] = df['response_time_min'] / df['attack_duration_min']
df['delayed_response'] = df.apply(lambda row: 1 if row['response_time_min'] > row['attack_duration_min'] else 0,axis=1)

print("\nHigh Risk Count:")
print(df['high_risk'].value_counts())

print("\nAttack Success Count:")
print(df['attack_success'].value_counts())

print("\nDelayed Response Count:")
print(df['delayed_response'].value_counts())

print("\nFinal Columns:")
print(df.columns)


# preparing data for modeling
df_ml = df.copy()
df_ml = pd.get_dummies(df_ml, drop_first=True)

print("\nEncoded Data Shape:", df_ml.shape)

# removing leakage columns
leakage_cols = [
    'high_risk',
    'attack_severity',
    'timestamp'
]

X = df_ml.drop(columns=leakage_cols, errors='ignore')
X = X.drop(columns=[col for col in X.columns if col.startswith('severity_label_')])
X = X.drop(columns=['data_compromised_GB'], errors='ignore')

y = df_ml['high_risk']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\nClassification Report After Model Balancing:\n")
print(classification_report(y_test, y_pred))

# feature importance
importance = pd.Series(model.feature_importances_, index=X.columns)
importance = importance.sort_values(ascending=False)

print("\nTop 10 Important Features After Leakage Fix:\n")
print(importance.head(10))

#saving cleaned dataset
df.to_csv("(path)/cybersecurity_synthesized_data_cleaned.csv", index=False)
print("\n Cleaned dataset saved successfully.")
