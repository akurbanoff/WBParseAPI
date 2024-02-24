from typing import Annotated

from fastapi import APIRouter

from src.parser.parser import parse_good

router = APIRouter(
    tags=["WB"]
)


@router.get('/get_good_wb')
def get_good_wb(article: str = "", good_url: str = ""):
    if good_url:
        article = good_url.split("/")[4]
    return parse_good(article=article)
