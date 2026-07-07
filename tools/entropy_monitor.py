#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ast: allow-subprocess
import os
import math
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_markdown_files(directories):
    files = []
    for d in directories:
        dir_path = os.path.join(ROOT, d)
        if not os.path.exists(dir_path):
            continue
        for root_dir, _, filenames in os.walk(dir_path):
            for f in filenames:
                if f.endswith('.md'):
                    files.append(os.path.relpath(os.path.join(root_dir, f), ROOT).replace('\\', '/'))
    return files

def tokenize(text):
    # Simple tokenization: lowercase, extract alphanumeric words >= 3 chars
    text = text.lower()
    words = re.findall(r'\b[a-zа-я0-9]{3,}\b', text)
    return words

def get_sentences(text):
    # Very basic sentence splitting
    lines = [line.strip() for line in text.replace('!', '.').replace('?', '.').split('.') if len(line.strip()) > 10]
    return lines

def compute_tf_idf(corpus_dict):
    # corpus_dict: {filepath: "text"}
    word_counts = {}
    doc_freq = Counter()
    
    for f, text in corpus_dict.items():
        tokens = tokenize(text)
        counts = Counter(tokens)
        word_counts[f] = counts
        doc_freq.update(counts.keys())
        
    N = len(corpus_dict)
    tf_idf = {}
    
    for f, counts in word_counts.items():
        tf_idf[f] = {}
        total_words = max(sum(counts.values()), 1)
        for word, count in counts.items():
            tf = count / total_words
            idf = math.log(N / (1 + doc_freq[word]))
            tf_idf[f][word] = tf * idf
            
    return tf_idf

def cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([val**2 for val in vec1.values()])
    sum2 = sum([val**2 for val in vec2.values()])
    
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return float(numerator) / denominator

def crystallize_shared_knowledge(file1, file2, text1, text2):
    # Extract sentences that share many words
    s1 = get_sentences(text1)
    s2 = get_sentences(text2)
    
    shared = []
    # Very naive intersection
    for sent in s1:
        tokens = set(tokenize(sent))
        if not tokens: continue
        # if this sentence has heavy overlap with any in s2
        for sent_b in s2:
            tokens_b = set(tokenize(sent_b))
            if len(tokens.intersection(tokens_b)) > 3:
                shared.append(sent)
                break
                
    # Create crystallized output
    name1 = os.path.basename(file1).replace('.md', '')
    name2 = os.path.basename(file2).replace('.md', '')
    crystal_filename = f"crystal_{name1}_{name2}.md"
    
    crystal_path = os.path.join(ROOT, 'indexes', crystal_filename)
    os.makedirs(os.path.dirname(crystal_path), exist_ok=True)
    
    content = [
        f"# Кристаллизация: {name1} и {name2}",
        "> [!NOTE]",
        "> Этот файл был сгенерирован алгоритмом Entropic Decay Monitor.",
        "> Оригинальные файлы сохранены в неприкосновенности.",
        "",
        "## Общие смысловые тезисы (пересечение)",
    ]
    
    if shared:
        for s in set(shared):
            content.append(f"- {s.capitalize()}.")
    else:
        content.append("- Смысловое пересечение обнаружено на уровне словаря, но точные тезисы не вычленены.")
        
    with open(crystal_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))
        
    return crystal_path

def main():
    dirs_to_scan = ['topics', 'decisions', 'tasks']
    files = get_markdown_files(dirs_to_scan)
    
    corpus = {}
    for f in files:
        path = os.path.join(ROOT, f)
        try:
            with open(path, 'r', encoding='utf-8') as file:
                corpus[f] = file.read()
        except Exception:
            pass
            
    print(f"Scanning {len(corpus)} files for entropy (duplicates)...")
    
    tf_idf = compute_tf_idf(corpus)
    file_list = list(corpus.keys())
    
    # We will track crystals created so we don't spam
    crystals_created = 0
    THRESHOLD = 0.65  # Lowered for demonstration, real world might need 0.8
    
    for i in range(len(file_list)):
        for j in range(i+1, len(file_list)):
            f1 = file_list[i]
            f2 = file_list[j]
            
            # Don't compare files in completely different domains if we want strictness, 
            # but we allow it for cross-pollination discovery.
            sim = cosine_similarity(tf_idf[f1], tf_idf[f2])
            if sim > THRESHOLD:
                print(f"Found high entropy overlap ({sim:.2f}): {f1} <-> {f2}")
                # Create a crystal
                if crystals_created < 5: # Limit for safety
                    c_path = crystallize_shared_knowledge(f1, f2, corpus[f1], corpus[f2])
                    print(f" -> Crystallized into {os.path.relpath(c_path, ROOT)}")
                    crystals_created += 1

    if crystals_created == 0:
        print("No high entropy overlaps found above threshold.")
    else:
        print(f"Total {crystals_created} crystals created. OLD FILES WERE NOT MODIFIED.")

if __name__ == "__main__":
    main()
