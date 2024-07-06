import os
from typing import Dict

from src.experimenting.helpers.markdown_file_writer import MarkdownFileWriter


def create_experiment_report(experiment_data: Dict):
    """
    Generate a comprehensive experiment report in Markdown format and save it to
    a file.

    Parameters:
        - experiment_data (dict): Dictionary containing experiment data.
    """
    report_path = os.path.join(experiment_data["directory"], "experiment_report.md")
    writer = MarkdownFileWriter(report_path)

    # Experiment Metadata
    writer.write_title(f"Experiment Report: {experiment_data['name']}", level=1)
    writer.write_title("Experiment Metadata", level=2)
    writer.write_key_value("Description", experiment_data["description"])
    writer.write_key_value("Start Time", experiment_data["start_time"])
    experiment_directory_link = writer.create_link(experiment_data["directory"], "Link")
    writer.write_key_value("Directory", experiment_directory_link)

    # Trials
    for trial in experiment_data.get("trials", []):
        writer.write_title(trial["name"], level=2)
        writer.write_key_value("Description", trial["description"])
        writer.write_key_value("Start Time", trial["start_time"])
        trial_directory_link = writer.create_link(trial["directory"], "Link")
        writer.write_key_value("Directory", trial_directory_link)
        hyperparameter_table = {
            param: str(value) for param, value in trial["hyperparameters"].items()
        }
        writer.write_title("Hyperparameters:", level=3)
        writer.write_key_value_table(
            hyperparameter_table, key_label="Hyperparameter", value_label="Value"
        )

        if "figures" in trial and trial["figures"]:
            writer.write_title("Figures:", level=3)
            for fig_name, fig_path in trial["figures"].items():
                writer.write_figure(fig_name, fig_path)

        if "evaluation_metrics" in trial and trial["evaluation_metrics"]:
            writer.write_title("Evaluation Metrics:", level=3)
            evaluation_metrics_table = {
                metric: f"{value:.4f}"
                for metric, value in trial["evaluation_metrics"].items()
                if isinstance(value, (int, float))
            }
            writer.write_key_value_table(
                evaluation_metrics_table, key_label="Metric", value_label="Value"
            )

    # Save the report
    writer.save_file()
