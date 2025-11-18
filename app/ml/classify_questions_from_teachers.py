import os
import numpy as np
import torch
import joblib
from tqdm import tqdm
from transformers import BertTokenizer, BertModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "question_auto_labels")

TOKENIZER = None
BERT = None

def build_bert(model_name="bert-base-chinese"):
    global TOKENIZER, BERT
    if TOKENIZER is None:
        TOKENIZER = BertTokenizer.from_pretrained(model_name)
        BERT = BertModel.from_pretrained(model_name)
        BERT.eval()
    return TOKENIZER, BERT


def extract_cls_embeddings(bert, tokenizer, texts, max_length=128, batch_size=16):
    all_embs = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Extracting BERT CLS"):
        batch = texts[i:i + batch_size]
        enc = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        with torch.no_grad():
            out = bert(**enc)
            cls = out.last_hidden_state[:, 0, :].cpu().numpy()
            all_embs.append(cls)
    return np.vstack(all_embs)

def auto_labels(question: str, answer: str):
    tokenizer, bert = build_bert()
    clf_type = joblib.load(os.path.join(MODEL_DIR, "clf_type.pkl"))
    clf_prop = joblib.load(os.path.join(MODEL_DIR, "clf_prop.pkl"))
    clf_diff = joblib.load(os.path.join(MODEL_DIR, "clf_diff.pkl"))
    mlb_type = joblib.load(os.path.join(MODEL_DIR, "mlb_type.pkl"))
    mlb_prop = joblib.load(os.path.join(MODEL_DIR, "mlb_prop.pkl"))
    le_diff = joblib.load(os.path.join(MODEL_DIR, "le_diff.pkl"))
    best_thr_type = joblib.load(os.path.join(MODEL_DIR, "best_thr_type.pkl"))
    best_thr_prop = joblib.load(os.path.join(MODEL_DIR, "best_thr_prop.pkl"))

    text = question + " 答案：" + answer
    X = extract_cls_embeddings(bert, tokenizer, [text])

    type_scores = clf_type.decision_function(X)[0]
    candidate_indices = [i for i, score in enumerate(type_scores) if score >= best_thr_type[i]]
    candidate_labels = [mlb_type.classes_[i] for i in candidate_indices]
    if '无' not in candidate_labels:
        pred_type_labels = candidate_labels
    else:
        idx_none = mlb_type.classes_.tolist().index('无')
        score_none = type_scores[idx_none]
        other_candidate_indices = [i for i in candidate_indices if mlb_type.classes_[i] != '无']
        other_candidate_scores = [type_scores[i] for i in other_candidate_indices]
        if not other_candidate_scores:
            pred_type_labels = ['无']
        else:
            if score_none >= max(other_candidate_scores):
                pred_type_labels = ['无']
            else:
                pred_type_labels = [lbl for lbl in candidate_labels if lbl != '无']

    prop_scores = clf_prop.decision_function(X)[0]
    pred_prop_labels = [
        mlb_prop.classes_[i]
        for i, score in enumerate(prop_scores)
        if score >= best_thr_prop[i]
    ]
    pred_diff = clf_diff.predict(X)
    pred_diff_label = le_diff.inverse_transform(pred_diff)[0]

    return pred_type_labels, pred_prop_labels, pred_diff_label

