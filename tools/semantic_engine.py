import math
import re
import hashlib
from collections import defaultdict, Counter

class AdvancedAlgorithms:
    # Маркеры отрицания для честной проверки противоречий (contradiction_check)
    NEGATIONS = {"не", "нет", "нельзя", "никогда", "нету",
                 "not", "no", "never", "cannot", "without", "без"}
    # Стоп-слова для дистрибутивных векторов (get_synonyms)
    STOPWORDS = {"и", "в", "на", "с", "по", "не", "что", "это", "как", "а",
                 "но", "для", "из", "у", "о", "же", "к", "то", "его", "их",
                 "the", "a", "an", "of", "to", "in", "and", "or", "is", "are"}

    @staticmethod
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return AdvancedAlgorithms.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    @staticmethod
    def extract_textrank_keywords(text, window_size=2, top_n=3, iterations=20, d=0.85):
        words = [w for w in re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', text.lower())
                 if w not in AdvancedAlgorithms.STOPWORDS]
        if not words: return []
        
        vocab = list(set(words))

        # Build adjacency matrix (dictionary of dictionaries)
        graph = defaultdict(lambda: defaultdict(float))
        for i in range(len(words)):
            for j in range(i + 1, min(i + window_size, len(words))):
                w1, w2 = words[i], words[j]
                if w1 != w2:
                    graph[w1][w2] += 1.0
                    graph[w2][w1] += 1.0
                    
        # Initialize PageRank
        pr = {w: 1.0 for w in vocab}
        
        # Power iteration
        for _ in range(iterations):
            new_pr = {}
            for node in vocab:
                rank_sum = 0
                for neighbor, weight in graph[node].items():
                    out_degree = sum(graph[neighbor].values())
                    if out_degree > 0:
                        rank_sum += weight * (pr[neighbor] / out_degree)
                new_pr[node] = (1 - d) + d * rank_sum
            pr = new_pr
            
        sorted_words = sorted(pr.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:top_n]]

    @staticmethod
    def extract_pmi_collocations(corpus, min_count=2, top_n=3):
        # corpus is list of strings
        unigram_counts = Counter()
        bigram_counts = Counter()
        total_unigrams = 0
        total_bigrams = 0
        
        for doc in corpus:
            words = re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', doc.lower())
            unigram_counts.update(words)
            total_unigrams += len(words)
            
            bigrams = list(zip(words[:-1], words[1:]))
            bigram_counts.update(bigrams)
            total_bigrams += len(bigrams)
            
        if total_bigrams == 0:
            return []
            
        pmi_scores = {}
        for (w1, w2), count in bigram_counts.items():
            if count >= min_count:
                p_w1 = unigram_counts[w1] / total_unigrams
                p_w2 = unigram_counts[w2] / total_unigrams
                p_w1w2 = count / total_bigrams
                pmi = math.log2(p_w1w2 / (p_w1 * p_w2))
                pmi_scores[f"{w1} {w2}"] = pmi
                
        sorted_pmi = sorted(pmi_scores.items(), key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_pmi[:top_n]]

    @staticmethod
    def extract_summary(text, max_sentences=3, d=0.85, iterations=20):
        """
        Extractive Summarization using TextRank on sentences.
        """
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        if len(sentences) <= max_sentences:
            return " ".join(sentences)
            
        # Function to calculate Jaccard-like similarity between two sentences
        def sentence_similarity(s1, s2):
            words1 = set(re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', s1.lower()))
            words2 = set(re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', s2.lower()))
            # ФИКС Б2: однословные предложения давали log10(1)=0 в знаменателе,
            # similarity взрывалась до ~1e9 и мусор захватывал PageRank.
            if len(words1) < 2 or len(words2) < 2: return 0.0
            return len(words1.intersection(words2)) / (math.log10(len(words1)) + math.log10(len(words2)) + 1e-9)

        # Build graph
        graph = defaultdict(lambda: defaultdict(float))
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                sim = sentence_similarity(sentences[i], sentences[j])
                if sim > 0:
                    graph[i][j] = sim
                    graph[j][i] = sim
                    
        # Power iteration
        pr = {i: 1.0 for i in range(len(sentences))}
        for _ in range(iterations):
            new_pr = {}
            for node in range(len(sentences)):
                rank_sum = 0
                for neighbor, weight in graph[node].items():
                    out_degree = sum(graph[neighbor].values())
                    if out_degree > 0:
                        rank_sum += weight * (pr[neighbor] / out_degree)
                new_pr[node] = (1 - d) + d * rank_sum
            pr = new_pr
            
        # Get top sentences
        top_sentences = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
        # Sort them back by original order to maintain flow
        top_sentences.sort(key=lambda x: x[0])
        
        return " ".join([sentences[idx] for idx, score in top_sentences])

    @staticmethod
    def get_synonyms(word, corpus, top_n=3):
        """
        Vector Semantics (LSA-lite): Finds synonyms by comparing context vectors.
        ФИКС Н1: раньше сравнивались сырые счётчики (докстринг обещал PMI) —
        метод возвращал контекстных СОСЕДЕЙ слова, а не его заменителей.
        Теперь: стоп-слова исключены из контекстов, вектора взвешены PPMI
        (positive pointwise mutual information) — сравниваются профили
        УДИВИТЕЛЬНОСТИ контекстов, что и даёт дистрибутивные синонимы.
        """
        word = word.lower()
        co_occurrence = defaultdict(Counter)
        word_counts = Counter()
        STOP = AdvancedAlgorithms.STOPWORDS

        for doc in corpus:
            words = re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', doc.lower())
            word_counts.update(words)
            for i, w1 in enumerate(words):
                # Context window of size 2
                start = max(0, i - 2)
                end = min(len(words), i + 3)
                for j in range(start, end):
                    if i != j and words[j] not in STOP:
                        co_occurrence[w1][words[j]] += 1

        if word not in co_occurrence:
            return []

        # PPMI-взвешивание: ppmi(w,c) = max(0, log2(p(w,c) / (p(w)·p(c))))
        row_sum = {w: sum(v.values()) for w, v in co_occurrence.items()}
        col_sum = Counter()
        for w, v in co_occurrence.items():
            for c, n in v.items():
                col_sum[c] += n
        total = sum(row_sum.values()) or 1

        def ppmi_vector(w):
            out = {}
            rw = row_sum.get(w, 0)
            if not rw:
                return out
            for c, n in co_occurrence[w].items():
                ratio = (n * total) / (rw * col_sum[c]) if col_sum[c] else 0
                if ratio > 1:
                    out[c] = math.log2(ratio)
            return out

        # Calculate cosine similarity of PPMI vectors
        def cosine_sim(v1, v2):
            intersection = set(v1.keys()) & set(v2.keys())
            dot_product = sum(v1[x] * v2[x] for x in intersection)
            mag1 = math.sqrt(sum(x**2 for x in v1.values()))
            mag2 = math.sqrt(sum(x**2 for x in v2.values()))
            if mag1 * mag2 == 0: return 0.0
            return dot_product / (mag1 * mag2)

        target_vector = ppmi_vector(word)
        similarities = {}
        for other_word in co_occurrence:
            if other_word != word and other_word not in STOP and word_counts[other_word] >= 2:
                similarities[other_word] = cosine_sim(target_vector, ppmi_vector(other_word))

        sorted_sim = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        return [w for w, score in sorted_sim[:top_n] if score > 0.1]

    @staticmethod
    def anomaly_detection(text):
        """
        Anomaly & Sentiment Detection: Calculates the density of negative markers.
        Returns a score (0.0 to 1.0) indicating the likelihood of AI being stuck.
        """
        markers = {"error", "fail", "broken", "missing", "cannot", "conflict",
                   "stuck", "loop", "wrong", "ошибка", "сбой", "завис"}
        # ФИКС Б3: «не могу» — двухсловный маркер, он никогда не совпадал
        # с однословными токенами. Фразовые маркеры ищем подстрокой в тексте.
        phrase_markers = ("не могу", "не получается", "give up", "same error")

        low = text.lower()
        words = re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', low)
        if not words: return 0.0

        marker_count = sum(1 for w in words if w in markers)
        for ph in phrase_markers:
            marker_count += low.count(ph)
        # If density is high (e.g., > 5% of words are negative markers), anomaly is high
        density = marker_count / len(words)
        
        # Normalize: 0.05 density -> 1.0 anomaly
        anomaly_score = min(1.0, density / 0.05)
        return anomaly_score

    @staticmethod
    def simhash(text):
        """
        Calculates a 64-bit SimHash for the text.
        Useful for Locality-Sensitive Hashing (LSH).
        """
        words = re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', text.lower())
        v = [0] * 64
        
        for word in words:
            # We need a stable hash. Built-in hash() is randomized in Python 3.
            # Using md5 (imported at module level) to generate a stable integer
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            for i in range(64):
                bit = (h >> i) & 1
                if bit:
                    v[i] += 1
                else:
                    v[i] -= 1
                    
        fingerprint = 0
        for i in range(64):
            if v[i] > 0:
                fingerprint |= (1 << i)
                
        return fingerprint

    @staticmethod
    def hamming_distance(h1, h2):
        """
        Calculates the Hamming distance between two 64-bit integers.
        """
        x = (h1 ^ h2) & ((1 << 64) - 1)
        return bin(x).count('1')

    @staticmethod
    def contradiction_check(text1, text2, hamming_threshold=20):
        """
        ФИКС Б1: честная проверка противоречия.
        Старый подход (Левенштейн > 0.8) был инвертирован: настоящее
        противоречие («X» vs «не X») текстуально БЛИЗКО (ratio ~0.06),
        а далёкие формулировки — чаще согласие, не спор.
        Новый критерий: тексты семантически/текстуально БЛИЗКИ
        (SimHash Hamming <= порога), но различаются ПОЛЯРНОСТЬЮ
        (числом маркеров отрицания).
        Возвращает {"related": bool, "contradicts": bool, "hamming": int}.
        """
        h = AdvancedAlgorithms.hamming_distance(
            AdvancedAlgorithms.simhash(text1), AdvancedAlgorithms.simhash(text2))
        related = h <= hamming_threshold

        def neg_count(t):
            ws = re.findall(r'\b[a-zA-Zа-яА-Я0-9_]+\b', t.lower())
            return sum(1 for w in ws if w in AdvancedAlgorithms.NEGATIONS)

        contradicts = bool(related and neg_count(text1) != neg_count(text2))
        return {"related": related, "contradicts": contradicts, "hamming": h}


