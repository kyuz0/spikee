"""
spikee/targets/generate_file.py

Target used to generate files based on a dataset.

Usage:

"""


from spikee.templates.target import Target

from dotenv import load_dotenv
from docx import Document
from fpdf import FPDF
import os
import requests
from typing import Optional, List


class GenerateFilesTarget(Target):

    _OPTIONS: List[str] = ["all", "pdf", "docx", "txt"]
    _DEFAULT_OPTION = "all"

    def get_available_option_values(self) -> List[str]:
        """Returns a list of supported option values, first is default. None if no options."""
        options = [self._DEFAULT_OPTION]
        options.extend([option for option in self._OPTIONS if option != self._DEFAULT_OPTION])
        return options

    def process_input(
        self,
        input_text: str,
        system_message: Optional[str] = None,
        target_options: Optional[str] = None,
        input_id: Optional[str] = None,
        output_file: Optional[str] = None,
    ) -> str:
        #  == Option Validation ==
        options = target_options.split(",") if target_options else [self._DEFAULT_OPTION]
        for option in options:
            if option not in self._OPTIONS:
                valid = ", ".join(self.get_available_option_values())
                raise ValueError(f"Unknown option value '{option}'. Valid options: {valid}")

        # == Output Location ==
        if input_id is None:
            raise ValueError("input_id must be provided for file generation.")

        if output_file is None:
            output_file = "results\\undefined.jsonl"

        files_dir = f"generated_files/{output_file.removesuffix('.jsonl').removeprefix('results\\')}/"
        os.makedirs(files_dir, exist_ok=True)

        #  == File Creation Logic ==
        try:
            # PDF
            if 'all' in options or 'pdf' in options:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, input_text)
                pdf.output(f"{files_dir}{input_id}.pdf")

            # DOCX
            if 'all' in options or 'docx' in options:
                doc = Document()
                doc.add_paragraph(input_text)
                doc.save(f"{files_dir}{input_id}.docx")

            # TXT
            if 'all' in options or 'txt' in options:
                with open(f"{files_dir}{input_id}.txt", "w", encoding="utf-8") as txt_file:
                    txt_file.write(input_text)

            return "Files generated successfully."

        except requests.exceptions.RequestException as e:
            print(f"Error generating file: {e}")
            raise
