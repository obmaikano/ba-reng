"""Tests for the standalone Motion document parser."""

from unittest.mock import patch

from backend.parse.motion import parse_pdf

NOTICE_OF_MOTIONS = (
    'BOTSWANA NATIONAL ASSEMBLY\n'
    'N O T I C E P A P E R\n'
    '(THURSDAY 26TH FEBRUARY, 2026)\n'
    'NOTICE OF MOTIONS\n'
    '(FOR FRIDAY 27TH FEBRUARY, 2026)\n'
    'DOMESTICATION OF THE SADC MODEL LAW\n'
    'ON PUBLIC FINANCE MANAGEMENT\n'
    '1. “That this Honourable House resolves to request Government to take the\n'
    'necessary steps to ratify and domesticate the SADC Model Law on Public\n'
    'Finance Management into the national Legal Framework.”\n'
    '(Mr. T. Furniture, MP. – Tati East)\n'
    'AMENDMENT OF THE PUBLIC HEALTH ACT\n'
    '2. “That this Honourable House requests Government to amend the Public\n'
    'Health Act in order to give the Director of Health Services powers.”\n'
    '(Mr. L. Lesedi, MP. – Serowe South)\n'
)

DEBATE_TRANSCRIPT_MOTION = (
    'PRIVATE MEMBERS MOTION - National Eco-Tourism Fund\n'
    'MOVED BY: HON. K. GOBOTSWANG (TSWAPONG SOUTH)\n'
    'SECONDED BY: MR. A. K. KHAN (MOLEPOLOLE NORTH)\n'
)


class TestParsePdfNoticeOfMotions:
    @patch('backend.parse.motion.extract_text', return_value=NOTICE_OF_MOTIONS)
    def test_extracts_every_motion_in_the_list(self, _mock_extract) -> None:
        results = parse_pdf('fake.pdf', 'https://example.com')

        assert len(results) == 2
        assert results[0]['raw_match_name'] == 'Mr. T. Furniture'
        assert results[0]['raw_constituency'] == 'Tati East'
        assert 'SADC Model Law' in results[0]['subject_text']
        assert results[1]['raw_match_name'] == 'Mr. L. Lesedi'
        assert results[1]['raw_constituency'] == 'Serowe South'

    @patch('backend.parse.motion.extract_text', return_value=NOTICE_OF_MOTIONS)
    def test_does_not_match_motion_inside_motions_header(self, _mock_extract) -> None:
        results = parse_pdf('fake.pdf', 'https://example.com')

        for r in results:
            assert r['subject_text'] != 'S'
            assert len(r['subject_text']) > 10


class TestParsePdfDebateTranscriptFallback:
    @patch('backend.parse.motion.extract_text', return_value=DEBATE_TRANSCRIPT_MOTION)
    def test_falls_back_to_moved_by_seconded_by_format(self, _mock_extract) -> None:
        results = parse_pdf('fake.pdf', 'https://example.com')

        assert len(results) == 2
        assert results[0]['raw_match_name'].startswith('HON. K. GOBOTSWANG')
        assert results[1]['raw_match_name'].startswith('MR. A. K. KHAN')


class TestParsePdfEmpty:
    @patch('backend.parse.motion.extract_text', return_value='no motion content here')
    def test_returns_empty_list_when_nothing_matches(self, _mock_extract) -> None:
        assert parse_pdf('fake.pdf', 'https://example.com') == []
