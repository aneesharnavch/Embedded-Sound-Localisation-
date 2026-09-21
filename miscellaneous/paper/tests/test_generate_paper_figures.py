import tempfile
import unittest
from pathlib import Path

from figures.generate_paper_figures import FIGURE_STEMS, bias_floor_rmse, generate_all


class PaperFigureTests(unittest.TestCase):
    def test_bias_floor_curve_reproduces_reported_rt60_030_value_at_t4(self):
        # Hand-checked from sqrt(1.977^2 + 1.272^2 / 4).
        self.assertAlmostEqual(bias_floor_rmse(4, 1.977, 1.272), 2.077, places=3)

    def test_generate_all_writes_each_publication_figure_as_png_and_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            generated = generate_all(output_dir)

            expected = {
                output_dir / f'{stem}.{suffix}'
                for stem in FIGURE_STEMS
                for suffix in ('png', 'svg')
            }
            self.assertEqual(set(generated), expected)

            for path in expected:
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 1_000, path)

            for stem in FIGURE_STEMS:
                png = (output_dir / f'{stem}.png').read_bytes()
                svg = (output_dir / f'{stem}.svg').read_text(encoding='utf-8')
                self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
                self.assertIn('<svg', svg)
                self.assertIn('rebaseline_results.md', svg)


if __name__ == '__main__':
    unittest.main()
