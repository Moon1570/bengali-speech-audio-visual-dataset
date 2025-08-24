# Bengali Text Normalization Guidelines

## Overview
This document outlines the text normalization choices made for the Bengali Speech Audio-Visual Dataset for consistent processing across Google Speech-to-Text and Whisper transcripts.

## Normalization Rules Applied

### 1. Unicode Normalization
- **Rule**: Apply NFC (Canonical Decomposition followed by Canonical Composition)
- **Rationale**: Ensures consistent representation of Bengali characters and combining marks
- **Example**: Decomposed characters are recomposed into their canonical form

### 2. Whitespace Handling
- **Rule**: Collapse multiple consecutive whitespace characters into single spaces
- **Rule**: Strip leading and trailing whitespace
- **Rationale**: ASR systems often introduce inconsistent spacing

### 3. Punctuation Normalization
- **Rule**: Normalize punctuation variants to standard forms
  - Smart quotes → straight quotes
  - Various dashes → standard dash
  - Multiple periods → single period or ellipsis
- **Rationale**: Different ASR systems output different punctuation variants

### 4. Digit Handling
- **Current Choice**: Keep both Bengali (০১২৩৪৫৬৭৮৯) and Latin (0123456789) digits as-is
- **Alternative**: Could normalize all to Bengali or all to Latin consistently
- **Rationale**: The charset analysis shows mostly Latin digits (25 occurrences) vs minimal Bengali digits
- **Recommendation**: Consider normalizing to Latin digits for consistency

### 5. Case Handling
- **Rule**: Preserve original case (Bengali doesn't have case, but Latin characters do)
- **Rationale**: Maintain semantic meaning where case might be significant

## Character Set Statistics

From analysis of training data (102 samples, 204 transcripts):

| Category | Count | Most Frequent |
|----------|-------|---------------|
| Bengali Letters | 38 chars | র (684×), ন (548×), ক (442×) |
| Bengali Marks | 12 chars | া (1044×), ে (851×), ি (521×) |
| Latin Digits | 8 chars | 0,5,1,3,7,2,8,9 |
| Punctuation | 5 chars | . , - " ' |
| Whitespace | 1 char | space (1704×) |

**Total**: 65 unique characters + CTC blank = 66 tokens for model training

## Quality Observations

### Common ASR Issues Observed:
1. **Inconsistent spacing** around punctuation
2. **Variant spellings** of the same word
3. **Missing or extra punctuation**
4. **Different transliterations** of foreign words (Facebook → ফেসবুক/ফেইসবুক)

### Gold Standard Guidelines:
- Use the more complete/longer transcript when available
- Maintain natural Bengali spelling conventions
- Standardize foreign word transliterations
- Preserve semantic punctuation, remove filler punctuation

## Implementation
Text normalization is implemented in:
- `experiments/multimodal_compare/src/utils/text_norm.py`
- Used by charset generation and evaluation scripts

## Future Considerations
1. Consider more aggressive normalization for evaluation metrics
2. May need speaker-specific normalization rules
3. Handle code-mixing (Bengali-English) more systematically
4. Standardize number representation (Bengali vs Latin digits)

---
*Generated on: 2025-08-24*  
*Dataset: Bengali Speech Audio-Visual Dataset*  
*Branch: exp-avsr-week1*
