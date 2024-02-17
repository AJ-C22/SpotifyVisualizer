import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

data = {'Category': ['Category A', 'Category B', 'Category C', 'Category D', 'Category E','Category F', 'Category G', 'Category H', 'Category I', 'Category J'],
        'Value': [10, 20, 15, 25, 30, 32, 41, 10, 15, 23]}

# Create a DataFrame
df = pd.DataFrame(data)

# Create a barplot
ax = sns.barplot(x='Category', y='Value', data=df)

# Adjust the tick positions and labels
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

# Show the plot
plt.show()