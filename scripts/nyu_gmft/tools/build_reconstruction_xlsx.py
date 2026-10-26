"""
nyu_gmft/tools/build_reconstruction_xlsx.py

Generates deliverables/02_MIRR_Assignment_Reconstruction.xlsx
Replicating the visual schema of Example song chart.xlsx:
- Block = 2 bars (at 120 bpm, 4/4 meter = 4.0 seconds per block)
- Header metadata: Artist - Song, Year, Meter, Tempo, Key
- Disclaimer: MIRR / AUXILIARY MACHINE ANALYSIS — VALIDATION ONLY — NOT FOR SUBMISSION
- Sections in Row 9 with bar counts
- Candidate sound sources with color-coded active blocks
"""

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from pathlib import Path

def create_reconstruction_xlsx(output_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Arrangement Chart (MIRR)"

    # Styles
    font_bold = Font(name="Arial", size=10, bold=True)
    font_regular = Font(name="Arial", size=9)
    font_title = Font(name="Arial", size=11, bold=True)
    font_disclaimer = Font(name="Arial", size=9, bold=True, color="990000")

    fill_gray_header = PatternFill(start_color="FFEFEFEF", end_color="FFEFEFEF", fill_type="solid")
    fill_drum = PatternFill(start_color="FFBF9000", end_color="FFBF9000", fill_type="solid")       # Gold/Amber
    fill_bass = PatternFill(start_color="FFE06666", end_color="FFE06666", fill_type="solid")       # Red/Coral
    fill_synth = PatternFill(start_color="FF6FA8DC", end_color="FF6FA8DC", fill_type="solid")      # Blue
    fill_guitar = PatternFill(start_color="FF93C47D", end_color="FF93C47D", fill_type="solid")     # Green
    fill_lead_vox = PatternFill(start_color="FFB4A7D6", end_color="FFB4A7D6", fill_type="solid")   # Purple
    fill_layer = PatternFill(start_color="FFF9CB9C", end_color="FFF9CB9C", fill_type="solid")      # Peach

    thin_border_side = Side(border_style="thin", color="CCCCCC")
    grid_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    # 1. Header Metadata
    ws["B1"] = "Mitski - Why Didn't You Stop Me"
    ws["B1"].font = font_title
    ws["F1"] = "(each block = 2 bars @ 120 BPM = 4.0s)"
    ws["F1"].font = font_regular

    ws["B2"] = "Source: 'Be the Cowboy' (2018)"
    ws["B2"].font = font_regular

    ws["B3"] = "MIRR / AUXILIARY MACHINE ANALYSIS — VALIDATION ONLY — NOT FOR SUBMISSION"
    ws["B3"].font = font_disclaimer

    ws["B5"] = "Meter - 4/4 (Defensible from 120.02 BPM Essentia & Librosa grid lock)"
    ws["B5"].font = font_regular
    ws["B6"] = "Tempo - 120 BPM [Essentia 120.02 | Librosa 119.68 | Std Dev 0.006s]"
    ws["B6"].font = font_regular
    ws["B7"] = "Key - D minor [Krumhansl-Kessler Chroma Correlation = 0.5550]"
    ws["B7"].font = font_regular

    # Timeline layout: Total 36 blocks (72 bars = 144 seconds)
    # Sections:
    # Blocks 1-1 (Cols B): Intro - 2 bars (0.0s - 4.0s)
    # Blocks 2-7 (Cols C-H): Section A1 - 12 bars (4.0s - 28.0s) [Verse feel]
    # Blocks 8-14 (Cols I-O): Section B1 - 14 bars (28.0s - 56.0s) [Chorus feel]
    # Blocks 15-19 (Cols P-T): Section A2 - 10 bars (56.0s - 76.0s) [Verse recurrence]
    # Blocks 20-25 (Cols U-Z): Section B2 - 12 bars (76.0s - 100.0s) [Chorus recurrence]
    # Blocks 26-33 (Cols AA-AH): Section C (Climax) - 16 bars (100.0s - 132.0s) [Climax/Instrumental]
    # Blocks 34-34 (Cols AI): Outro Hit - 2 bars (132.0s - 136.0s)
    # Blocks 35-36 (Cols AJ-AK): Decay/Tail - 4 bars (136.0s - 142.1s)

    section_spans = [
        (2, 2, "Intro - 2"),
        (3, 8, "Section A1 - 12"),
        (9, 15, "Section B1 - 14"),
        (16, 20, "Section A2 - 10"),
        (21, 26, "Section B2 - 12"),
        (27, 34, "Section C (Climax) - 16"),
        (35, 35, "Hit - 2"),
        (36, 37, "Decay - 4")
    ]

    total_cols = 37 # Col A (1) + 36 blocks (2 to 37)

    # Row 9: Section Headers
    ws.cell(9, 1, "Track / Sound Source [PROVENANCE]").font = font_bold
    ws.cell(9, 1).fill = fill_gray_header
    ws.cell(9, 1).border = grid_border

    for start_c, end_c, title in section_spans:
        for c in range(start_c, end_c + 1):
            cell = ws.cell(9, c)
            cell.fill = fill_gray_header
            cell.border = grid_border
            if c == start_c:
                cell.value = title
                cell.font = font_bold
                cell.alignment = Alignment(horizontal="left")

    # Define Candidate Tracks and their active column ranges
    tracks = [
        {
            "name": "Drum set (Kick/Snare/Hi-Hat) [AUX-HIGH]",
            "fill": fill_drum,
            "active_ranges": [(3, 34), (35, 35)] # Intro has sparse/synth; drums kick in bar 3 through climax hit
        },
        {
            "name": "Electric Bass / Synth Bass [AUX-HIGH]",
            "fill": fill_bass,
            "active_ranges": [(3, 34), (35, 35)] # Heavy bass drive across all main sections
        },
        {
            "name": "Keyboard / Synthesizer Pad [AUX-HIGH]",
            "fill": fill_synth,
            "active_ranges": [(2, 35)] # Present from intro pickup through outro hit
        },
        {
            "name": "Electric Guitar (Rhythm/Drive) [AUX-MED]",
            "fill": fill_guitar,
            "active_ranges": [(3, 15), (21, 34)] # Energetic driving sections and climax
        },
        {
            "name": "Lead Vocal (Centered) [AUX-HIGH]",
            "fill": fill_lead_vox,
            "active_ranges": [(3, 15), (16, 26)] # Verses and choruses; drops in climax
        },
        {
            "name": "Widened Layers (Horns/Synths/BGV) [AUX-MED]",
            "fill": fill_layer,
            "active_ranges": [(9, 15), (21, 34)] # Expansion in choruses and peak climax
        },
        {
            "name": "Amapiano Log Drum [MIRR-FALSE POSITIVE]",
            "fill": None, # DELIBERATELY EMPTY TO REFLECT SCIENTIFIC TRUTH
            "active_ranges": [] # NOT PRESENT in physical audio!
        }
    ]

    row_start = 10
    for idx, t in enumerate(tracks):
        r = row_start + idx
        name_cell = ws.cell(r, 1, t["name"])
        name_cell.font = font_regular
        name_cell.border = grid_border

        active_cols = set()
        for c_start, c_end in t["active_ranges"]:
            for c in range(c_start, c_end + 1):
                active_cols.add(c)

        for c in range(2, total_cols + 1):
            cell = ws.cell(r, c)
            cell.border = grid_border
            if c in active_cols and t["fill"] is not None:
                cell.fill = t["fill"]

    # Adjust column widths
    ws.column_dimensions["A"].width = 44
    for c in range(2, total_cols + 1):
        col_letter = openpyxl.utils.get_column_letter(c)
        ws.column_dimensions[col_letter].width = 4.2

    # Save
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_p))
    print(f"Reconstruction spreadsheet successfully created at: {out_p}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "deliverables/02_MIRR_Assignment_Reconstruction.xlsx"
    create_reconstruction_xlsx(out)
