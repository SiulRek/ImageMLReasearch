import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix


def plot_confusion_matrix(y_true, y_pred, class_names):
    """
    Plots a confusion matrix using Matplotlib and Seaborn.

    Parameters:
        - y_true: Array-like of true labels.
        - y_pred: Array-like of predicted labels.
        - class_names: List of class names corresponding to the
            labels.

    Returns:
        - fig: The Matplotlib figure containing the confusion matrix plot.
    """
    # Configuration
    figsize = (len(class_names) + 2, len(class_names) + 2)
    fontsize = 12
    cmap = "Blues"
    fmt = "d"

    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        cm,
        annot=True,
        fmt=fmt,
        cmap=cmap,
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
        annot_kws={"fontsize": fontsize},
    )

    ax.set_xlabel("Predicted Labels", fontsize=int(fontsize * 1.3))
    ax.set_ylabel("True Labels", fontsize=int(fontsize * 1.3))
    ax.tick_params(axis="both", which="major", labelsize=fontsize)

    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=fontsize)

    plt.tight_layout()
    return fig
