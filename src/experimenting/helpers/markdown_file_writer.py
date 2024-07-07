import os


class MarkdownFileWriter:
    """
    A helper class to write to a Markdown file.

    Args:
        - file_path (str): The file path where the Markdown file will be
            saved.
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.file_dir = os.path.dirname(file_path)
        self.file_lines = []

    def write_title(self, title, level=1):
        """
        Writes a title to the file.

        Args:
            - title (str): The text of the title.
            - level (int, optional): The level of the title, where 1 is the
                highest level. Defaults to 1.
        """
        self.file_lines.append(f"{'#' * level} {title}\n")

    def write_text(self, text):
        """
        Writes a plain text paragraph to the file.

        Args:
            - text (str): The text to write.
        """
        self.file_lines.append(f"{text}\n")

    def write_key_value_table(self, table_data, key_label="Key", value_label="Value"):
        """
        Writes a table with key-value pairs, where each row contains a key and a
        value.

        Args:
            - table_data (dict[str, str]): Dictionary containing key-value
                pairs.
            - key_label (str, optional): Label of the key column. Defaults
                to "Key".
            - value_label (str, optional): Label of the value column.
                Defaults to "Value".
        """
        elements = list(table_data.keys()) + list(table_data.values())
        max_elem_len = max(len(elem) for elem in elements)

        key_header = f"{key_label}".ljust(max_elem_len)
        value_header = f"{value_label}".ljust(max_elem_len)

        self.file_lines.append(f"| {key_header} | {value_header} |")
        self.file_lines.append(f"| {'-' * max_elem_len} | {'-' * max_elem_len} |")
        for key, value in table_data.items():
            padded_key = f"{key}".ljust(max_elem_len)
            padded_value = f"{value}".ljust(max_elem_len)
            self.file_lines.append(f"| {padded_key} | {padded_value} |")
        self.file_lines.append("\n")

    def write_nested_table(self, nested_table_data):
        """
        Writes a nested table with outer keys as column headers and inner keys
        as row headers.

        Args:
            - nested_table_data (dict[str, dict[str, str]]): Dictionary of
                dictionaries.
        """

        def max_elem_length(elements):
            return max(len(elem) for elem in elements)

        if not nested_table_data:
            return
        headers = list(nested_table_data.keys())
        inner_dict = nested_table_data[headers[0]]
        row_labels = list(inner_dict.keys())

        max_elem_len = max_elem_length(headers + row_labels)
        for inner_dict in nested_table_data.values():
            previous_max_elem_len = max_elem_len
            max_elem_len = max_elem_length(inner_dict.keys())
            max_elem_len = max(max_elem_len, previous_max_elem_len)

        header_row = (
            f"| {' ' * max_elem_len} | "
            + " | ".join(header.ljust(max_elem_len) for header in headers)
            + " |"
        )
        self.file_lines.append(header_row)
        self.file_lines.append(
            f"| {'-' * max_elem_len} | "
            + " | ".join("-" * max_elem_len for _ in headers)
            + " |"
        )

        for label in row_labels:
            label = f"{label}"
            row = f"| {label.ljust(max_elem_len)} | "
            for header in headers:
                value = nested_table_data[header].get(label, "").ljust(max_elem_len)
                row += f"{value} | "
            self.file_lines.append(row)
        self.file_lines.append("\n")

    def write_figure(self, figure_name, path):
        """
        Writes a Markdown image link to the file.

        Args:
            - figure_name (str): The alt text for the figure.
            - path (str): The file path to the figure.
        """
        figure_link = self.create_link(path, figure_name)
        self.file_lines.append(f"!{figure_link}\n")

    def write_key_value(self, key, value):
        """
        Writes a key-value pair in bullet point format to the file.

        Args:
            - key (str): The key text.
            - value (str): The value text.
        """
        self.file_lines.append(f"*    {key}: {value}\n")

    def create_link(self, path, hyperlink_text=None):
        """
        Creates a Markdown hyperlink to a given path.

        Args:
            - path (str): The file path for the link.
            - hyperlink_text (str, optional): The hyperlink text. Defaults
                to "[Link]".

        Returns:
            - str: The Markdown formatted hyperlink.
        """
        relative_path = os.path.relpath(path, self.file_dir)
        markdown_path = relative_path.replace(os.sep, "/")
        link = f"./{markdown_path}"
        hyperlink_text = hyperlink_text or "[Link]"
        return f"[{hyperlink_text}]({link})"

    def save_file(self):
        """ Saves the file to the specified file path. """
        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(self.file_lines))

    def clear_file(self):
        """ Clears all the content of the current file. """
        self.file_lines = []
