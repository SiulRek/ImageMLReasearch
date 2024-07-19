import matplotlib.pyplot as plt


def _sanitize_histories(histories):
    """
    Sanitizes the histories dictionary by converting all values to lists.

    Args:
        - histories: Dictionary containing multiple histories in the format
            {Name: history}.

    Returns:
        - sanitized_histories: Dictionary containing multiple histories in the
            format - {Name: history}
        - known_metrics: List of known metrics in the histories.
    """
    sanitized_histories = {}
    known_metrics = list(next(iter(histories.values())).keys())
    for name, history in histories.items():
        sanitized_history = {}
        for metric in known_metrics:
            sanitized_history[metric] = history.get(metric, [])
        for metric in history:
            if metric not in known_metrics:
                sanitized_history[metric] = history[metric]
                known_metrics.append(metric)
        sanitized_histories[name] = sanitized_history
    return sanitized_histories, known_metrics


def plot_training_histories(histories):
    """
    Plots the training and validation histories of multiple Keras models.

    Args:
        - histories: Dictionary containing multiple histories in the format
        - {Name: history}

    Returns:
        - fig: The Matplotlib figure containing the combined training and
            validation history plot.
    """
    # Configuration
    font_size = 12
    default_fig_size = (10, 6)  # Assumes a single metric.

    # Sanitize all histories to have same metrics.
    histories, known_metrics = _sanitize_histories(histories)

    epochs = range(1, len(next(iter(histories.values()))[known_metrics[0]]) + 1)

    num_metrics = (
        len(known_metrics) // 2
        if any(key.startswith("val_") for key in known_metrics)
        else len(known_metrics)
    )
    fig_size = (default_fig_size[0], default_fig_size[1] * num_metrics)
    fig, axes = plt.subplots(num_metrics, 1, figsize=fig_size)

    if num_metrics == 1:
        axes = [axes]

    colors = plt.cm.get_cmap("tab20", len(histories))

    for idx, (history_name, history_dict) in enumerate(histories.items()):
        color = colors(idx)
        i = 0
        for metric in history_dict:
            if history_dict[metric] != [] and not metric.startswith("val_"):
                ax = axes[i]
                i += 1
                ax.plot(
                    epochs,
                    history_dict[metric],
                    label=f"{history_name} Training {metric}",
                    color=color,
                )
                if f"val_{metric}" in history_dict:
                    ax.plot(
                        epochs,
                        history_dict[f"val_{metric}"],
                        "--",
                        label=f"{history_name} Validation {metric}",
                        color=color,
                    )
                ax.set_xlabel("Epochs", fontsize=font_size)
                ax.set_ylabel(metric.capitalize(), fontsize=font_size)
                ax.tick_params(axis="x", labelsize=font_size)
                ax.tick_params(axis="y", labelsize=font_size)
                ax.legend(loc="best", fontsize=font_size)
                ax.grid(True)

    plt.tight_layout()
    return fig
