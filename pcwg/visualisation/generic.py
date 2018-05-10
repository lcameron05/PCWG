from matplotlib import pyplot as plt


def generic_histogram(df, col, grid_lines=True, no_of_bins=20, unit=None):
    df.hist(column=col, bins=no_of_bins)
    plt.xlim([df[col].min(), df[col].max()])
    x_label = col if not unit else col + ' (' + unit + ')'
    plt.xlabel(x_label)
    plt.ylabel("Data Count")
    plt.grid(grid_lines)
    plt.show()

def hour_of_day_histogam(df, grid_lines=True):
    df['Hour of Day'] = df.index.hour
    generic_histogram(df, 'Hour of Day', grid_lines=grid_lines, no_of_bins=24)
    df.drop('Hour of Day', axis=1, inplace=True)
