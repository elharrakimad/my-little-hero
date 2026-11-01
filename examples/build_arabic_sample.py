"""Offline Arabic typesetting check using existing illustrations, without AI calls."""
from pathlib import Path
from book_layout import build_book_pdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    return build_book_pdf(ROOT / "output/pdf/itar-arabic-verification.pdf", [{
        "title": "إيتار والسلة الحاسمة",
        "text": "وقف إيتار في الملعب ونظر إلى السلة. كان أصدقاؤه يشجعونه، والكرة بين يديه. قال بثقة: «سننجح معا، خطوة بعد خطوة!» مرر الكرة إلى صديقه، ثم ركض نحو السلة واستعادها في اللحظة المناسبة. قفز وسدد، فدخلت الكرة وسط فرحة الفريق. اكتشف إيتار أن النجاح لا يأتي من المهارة وحدها، بل من الشجاعة والتعاون أيضا.",
        "image": ROOT / "examples/itar/story-illustration-v2.png"}],
        ROOT / "examples/itar/medallion.png", child_name="إيتار", language="العربية",
        congratulations="لقد شجعت فريقك وسجلت السلة الحاسمة بشجاعة!", gender="boy")


if __name__ == "__main__":
    print(main())
