import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import async_session_maker
from app.core.config import settings
from app.services.retrieval.retrieval_service import retrieve_relevant_chunks
from app.services.rag.rag_service import generate_rag_answer
from app.models.base import Workspace, User

async def calculate_recall(retrieved_ids: List[int], gold_ids: List[int]) -> float:
    if not gold_ids:
        return 0.0
    intersection = set(retrieved_ids).intersection(set(gold_ids))
    return len(intersection) / len(gold_ids)

async def calculate_mrr(retrieved_ids: List[int], gold_ids: List[int]) -> float:
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in gold_ids:
            return 1.0 / i
    return 0.0

async def calculate_citation_validity(answer: str, retrieved_chunks: List[Any]) -> float:
    import re
    citations = re.findall(r"\[(\d+)\]", answer)
    if not citations:
        return 0.0

    valid = 0
    for cit in citations:
        idx = int(cit)
        if 1 <= idx <= len(retrieved_chunks):
            valid += 1
    return valid / len(citations)

async def run_eval_case(db: AsyncSession, case: Dict, top_k: int, threshold: float):
    # We need a workspace_id. For eval, we assume workspace 1 exists or we create one.
    workspace_id = 1

    # 1. Test Retrieval
    retrieved = await retrieve_relevant_chunks(
        db, case["question"], workspace_id, top_k=top_k, threshold=threshold
    )
    ret_ids = [c.chunk_id for c in retrieved]

    # 2. Test Full RAG
    # Note: we mock a conversation_id and user_id for eval
    answer, cited_ids = await generate_rag_answer(
        db, conversation_id=1, user_id=1, workspace_id=workspace_id, query_text=case["question"]
    )

    return {
        "recall": await calculate_recall(ret_ids, case["gold_chunk_ids"]),
        "mrr": await calculate_mrr(ret_ids, case["gold_chunk_ids"]),
        "validity": await calculate_citation_validity(answer, retrieved)
    }

async def main():
    with open("evaluation/datasets/eval_set.json", "r") as f:
        eval_set = json.load(f)

    top_k_values = [3, 5, 10]
    threshold_values = [0.6, 0.7, 0.8]

    print(f"Running evaluation on {len(eval_set)} cases...\n")

    async with async_session_maker() as db:
        for k in top_k_values:
            for t in threshold_values:
                total_recall = 0
                total_mrr = 0
                total_validity = 0

                for case in eval_set:
                    res = await run_eval_case(db, case, k, t)
                    total_recall += res["recall"]
                    total_mrr += res["mrr"]
                    total_validity += res["validity"]

                print(f"k={k}, t={t} -> Recall: {total_recall/len(eval_set):.3f}, MRR: {total_mrr/len(eval_set):.3f}, Validity: {total_validity/len(eval_set):.3f}")

if __name__ == "__main__":
    asyncio.run(main())
