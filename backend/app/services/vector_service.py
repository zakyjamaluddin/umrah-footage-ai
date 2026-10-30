import math
import json
from typing import List, Dict, Any, Tuple
import numpy as np
from app.database import get_all_scenes, get_setting

# Simple robust semantic & term vector indexer
class SceneVectorIndex:
    _embeddings_cache: Dict[int, List[float]] = {}
    
    @classmethod
    def _get_text_representation(cls, scene: Dict[str, Any]) -> str:
        tags = " ".join(scene.get("tags", []))
        suitability = " ".join(scene.get("suitability", []))
        loc = scene.get("location", "")
        desc = scene.get("visual_description", "")
        mood = scene.get("mood", "")
        pacing = scene.get("pacing", "")
        return f"{desc} | Lokasi: {loc} | Mood: {mood} | Tempo: {pacing} | Tag: {tags} | Cocok untuk: {suitability}"

    @classmethod
    def _cosine_similarity(cls, v1: List[float], v2: List[float]) -> float:
        a = np.array(v1)
        b = np.array(v2)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @classmethod
    def get_embedding(cls, text: str, api_key: str = None) -> List[float]:
        """Generate embedding using Gemini text-embedding-004 if API key exists, or robust hash-weighted TF fallback."""
        key = api_key or get_setting("gemini_api_key")
        if key:
            try:
                from google import genai
                client = genai.Client(api_key=key)
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text,
                )
                if response.embeddings and len(response.embeddings) > 0:
                    return response.embeddings[0].values
            except Exception as e:
                pass
        
        # Fallback local pseudo-embedding (Bag of words / hash vector)
        dim = 256
        vec = np.zeros(dim)
        words = text.lower().replace("-", " ").replace(",", " ").replace(".", " ").split()
        for i, word in enumerate(words):
            h = hash(word) % dim
            vec[h] += 1.0 + (1.0 / (i + 1))
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @classmethod
    def index_scene(cls, scene_id: int, scene_data: Dict[str, Any], api_key: str = None):
        text = cls._get_text_representation(scene_data)
        emb = cls.get_embedding(text, api_key)
        cls._embeddings_cache[scene_id] = emb

    @classmethod
    def search_similar_scenes(cls, query_text: str, top_k: int = 5, preferred_mood: str = None, api_key: str = None) -> List[Dict[str, Any]]:
        scenes = get_all_scenes()
        if not scenes:
            return []

        query_emb = cls.get_embedding(query_text, api_key)
        scored_scenes: List[Tuple[float, Dict[str, Any]]] = []

        for scene in scenes:
            scene_id = scene["id"]
            if scene_id not in cls._embeddings_cache:
                cls.index_scene(scene_id, scene, api_key)
            
            scene_emb = cls._embeddings_cache[scene_id]
            sim = cls._cosine_similarity(query_emb, scene_emb)
            
            # Mood boost
            if preferred_mood and preferred_mood.lower() in scene.get("mood", "").lower():
                sim += 0.15
            
            # Simple keyword overlap boost
            query_terms = set(query_text.lower().split())
            scene_terms = set(cls._get_text_representation(scene).lower().split())
            overlap = len(query_terms.intersection(scene_terms))
            sim += (overlap * 0.05)

            score = min(round(sim * 100, 1), 99.9)
            scored_scenes.append((score, scene))

        scored_scenes.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, scene in scored_scenes[:top_k]:
            res = dict(scene)
            res["relevance_score"] = score
            results.append(res)
            
        return results
