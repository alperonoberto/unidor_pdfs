import tempfile
import unittest
from pathlib import Path

from unidor_pdfs.pdf_files import collect_pdf_files


class CollectPdfFilesTests(unittest.TestCase):
    def test_accepts_pdf_files_in_order_and_skips_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "primer archivo.pdf"
            second = Path(directory) / "SEGUNDO.PDF"
            first.touch()
            second.touch()

            new_files, rejected_count = collect_pdf_files(
                [str(first)],
                [str(first), str(second), str(second)],
            )

        self.assertEqual(new_files, [str(second.resolve())])
        self.assertEqual(rejected_count, 0)

    def test_rejects_non_pdf_and_missing_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            text_file = Path(directory) / "documento.txt"
            text_file.touch()
            missing_pdf = Path(directory) / "inexistente.pdf"

            new_files, rejected_count = collect_pdf_files(
                [],
                [str(text_file), str(missing_pdf)],
            )

        self.assertEqual(new_files, [])
        self.assertEqual(rejected_count, 2)


if __name__ == "__main__":
    unittest.main()
