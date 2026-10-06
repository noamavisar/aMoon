# from pathlib import Path
# import os
# from deck_extractor import (
#     extract_pptx_text,
#     DeckExtractionError,
#     parse_pptx_document,
# )



# def atomic_write_text(
#     path: Path,
#     content: str,
# ) -> None:
#     path.parent.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     temp_path = path.with_suffix(
#         path.suffix + ".tmp"
#     )

#     temp_path.write_text(
#         content,
#         encoding="utf-8",
#     )

#     os.replace(
#         temp_path,
#         path,
#     )

# class DeckExtractionError(Exception):
#     pass


# pptx_path = Path(
#     'hepler_files\\AgileRPM - Investment Pitch Deck.pptx'
# )

# data = pptx_path.read_bytes()

# # result = extract_pptx_text(data)
# parsed = parse_pptx_document(data)

# print("Slides:", parsed.page_count)
# print("Characters:", parsed.char_count)
# print()
# print(parsed.full_text)


# # if result["char_count"] == 0:
# #     raise DeckExtractionError(
# #         "No extractable text was found in the deck."
# #     )

# # MIN_DECK_TEXT_CHARS = 200

# # if result["char_count"] < MIN_DECK_TEXT_CHARS:
# #     raise DeckExtractionError(
# #         "Too little extractable text was found in the deck."
# #     )




# # print("Slides:", result["slide_count"])
# # print(
# #     "Slides with text:",
# #     result["nonempty_slide_count"],
# # )
# # print("Characters:", result["char_count"])
# # print()
# # print(result["full_text"])

# # opportunity_dir = Path(
# #     "data/test_agilerpm"
# # )

# # deck_text_path = (
# #     opportunity_dir / "deck.txt"
# # )

# # atomic_write_text(
# #     deck_text_path,
# #     result["full_text"],
# # )

# # print()
# # print(
# #     f"Deck text saved to: {deck_text_path}"
# # )
from pathlib import Path

from deck_extractor import (
    parse_pptx_document,
    DeckExtractionError,
)


pptx_path = Path(
    "hepler_files/AgileRPM - Investment Pitch Deck.pptx"
)

try:
    data = pptx_path.read_bytes()

    parsed = parse_pptx_document(data)

    print("Slides:", parsed.page_count)
    print("Characters:", parsed.char_count)
    print("SHA256:", parsed.sha256)

    print()
    print(parsed.full_text)

except DeckExtractionError as exc:
    print(
        f"Deck extraction failed: {exc}"
    )