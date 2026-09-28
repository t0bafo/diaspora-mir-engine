"""
nyu_gmft/tools/build_onepager_pdf.py

Builds a clean, publication-grade 1-page PDF audit summary using ReportLab.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pathlib import Path

def generate_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#1A237E')
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#B71C1C')
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0D47A1'),
        spaceBefore=4,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        'BodyTxt',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#212121')
    )
    bold_body_style = ParagraphStyle(
        'BoldBodyTxt',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#212121')
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor('#212121')
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor('#1A237E')
    )

    elements = []

    # Title & Subtitle
    elements.append(Paragraph("MIRR AUDITION AUDIT — ONE-PAGE SUMMARY", title_style))
    elements.append(Paragraph("VALIDATION ONLY — BLIND EXPERIMENT PHASE — NOT FOR SUBMISSION", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A237E'), spaceAfter=4, spaceBefore=3))

    # Track Metadata
    meta_text = (
        "<b>Track:</b> Mitski – <i>Why Didn't You Stop Me</i> | "
        "<b>Duration:</b> 142.12s (2:22) | "
        "<b>SHA-256:</b> f67539f6670599a3... | "
        "<b>MIRR:</b> v1.3.0 (Commit 492eda2) | "
        "<b>Status:</b> <b>SEVERELY OUT-OF-DISTRIBUTION (OOD)</b>"
    )
    elements.append(Paragraph(meta_text, body_style))
    elements.append(Spacer(1, 3))

    # Native MIRR Read Table
    elements.append(Paragraph("1. NATIVE MIRR READ", h2_style))
    table_data = [
        [
            Paragraph("<b>Metric</b>", table_cell_bold),
            Paragraph("<b>Value</b>", table_cell_bold),
            Paragraph("<b>Provenance</b>", table_cell_bold),
            Paragraph("<b>Extractor / Method</b>", table_cell_bold),
            Paragraph("<b>Reliability & Diagnostic Note</b>", table_cell_bold),
        ],
        [
            Paragraph("Tempo / BPM", table_cell_style),
            Paragraph("<b>120.02</b>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("Essentia RhythmExtractor2013", table_cell_style),
            Paragraph("Flawless lock to 120.0 BPM DAW click / drum grid", table_cell_style),
        ],
        [
            Paragraph("Pulse Clarity", table_cell_style),
            Paragraph("<b>0.8279</b>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("Onset Autocorrelation @ Beat Lag", table_cell_style),
            Paragraph("Exceptionally high metronomic regularity", table_cell_style),
        ],
        [
            Paragraph("Syncopation", table_cell_style),
            Paragraph("<b>0.2622</b>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("16th-Note Offbeat Ratio", table_cell_style),
            Paragraph("Restrained offbeat density; straight driving rock feel", table_cell_style),
        ],
        [
            Paragraph("Rhythmic Complexity", table_cell_style),
            Paragraph("<b>0.5066</b>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("IOI Coeff. of Variation (tanh)", table_cell_style),
            Paragraph("Moderate variation introduced by vocal and melodic fills", table_cell_style),
        ],
        [
            Paragraph("Log-Drum Signature", table_cell_style),
            Paragraph("<font color='#D32F2F'><b>1.0000</b></font>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("Sub-Bass Ratio + Onset Centroid", table_cell_style),
            Paragraph("<b>CRITICAL FALSE POSITIVE</b> (saturated by rock bass/kick)", table_cell_style),
        ],
        [
            Paragraph("Custom Danceability", table_cell_style),
            Paragraph("<font color='#D32F2F'><b>0.6926</b></font>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("0.50*PC + 0.30*Sync + 0.20*LogDrum", table_cell_style),
            Paragraph("Artificially inflated by false log drum (+0.20 contribution)", table_cell_style),
        ],
        [
            Paragraph("Energy RMS", table_cell_style),
            Paragraph("<b>0.2339</b>", table_cell_style),
            Paragraph("[MIRR]", table_cell_style),
            Paragraph("Essentia RMS (120s buffer)", table_cell_style),
            Paragraph("Reflects modern compressed, high-density master", table_cell_style),
        ]
    ]

    t = Table(table_data, colWidths=[90, 45, 40, 150, 215])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E8EAF6')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#C5CAE9')),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 3))

    # Interpretations & Auxiliary Findings
    elements.append(Paragraph("2. INTERPRETATIONS & AUXILIARY FINDINGS", h2_style))
    interp_text = (
        "• <b>Metronomic Engine:</b> 120.02 BPM and 0.8279 pulse clarity confirm a studio click-track rock anchor.<br/>"
        "• <b>The Log Drum Trap:</b> 61.59% of energy lies below 250 Hz (12.6% sub-bass, 49.0% bass). The v1.3.0 log drum detector saturated at 1.0, exposing severe domain vulnerability.<br/>"
        "• <b>Harmonic & Key Profile [AUX]:</b> Estimated key is <b>D Minor</b> (Krumhansl correlation 0.5550, followed by A minor 0.534 and F major 0.524). Harmonic/Percussive energy ratio is <b>2.21</b>.<br/>"
        "• <b>Spatial Architecture [AUX]:</b> Balanced commercial stereo (Width ratio = 0.4187, L/R corr = 0.7041) with anchored center phantom vocal and wide guitar/synth spreads.<br/>"
        "• <b>Dynamic Form [AUX]:</b> Energy ramps steadily into a dramatic climax at Bars 51–66 (t=100s–132s, RMS 0.364), ending in a sharp 2-bar cutoff hit."
    )
    elements.append(Paragraph(interp_text, body_style))
    elements.append(Spacer(1, 3))

    # Confidence, Limits & Checkpoints
    elements.append(Paragraph("3. CONFIDENCE, LIMITS & BLIND CHECKPOINTS", h2_style))
    limits_text = (
        "• <b>Strongest Machine Finding:</b> Absolute tempo extraction (120.0 BPM) and temporal grid stability (std dev = 0.006s).<br/>"
        "• <b>Weakest Machine Finding:</b> Timbral sound source classification — cannot isolate individual instruments without neural stem separation.<br/>"
        "• <b>Likely Domain-Shift Failure:</b> Algorithmic conflation of electric bass guitar transients with Amapiano FM log drums.<br/>"
        "• <b>Checkpoints Against Human Ears:</b> (1) Did you hear D minor / F major? (2) Did you note 120 BPM in 4/4? (3) What is the exact bass instrument (electric bass vs. synth)? (4) Did the drums enter in Bar 3? (5) What instruments drive the climax at 100s–132s (horns, distorted guitars)? (6) Does the false-positive 1.0 log drum highlight the necessity of genre gating before feature extraction?"
    )
    elements.append(Paragraph(limits_text, body_style))

    doc.build(elements)
    print(f"PDF successfully built at: {output_path}")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "deliverables/01_MIRR_Audit_OnePager.pdf"
    generate_pdf(out)
