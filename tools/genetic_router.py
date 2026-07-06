#!/usr/bin/env python3
import json
import os
import random

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENOME_FILE = os.path.join(ROOT, "indexes", "routing_genes.json")

# Agents pool
AGENTS = ["codex", "claude", "mavis", "novax", "summarizer", "reviewer"]

def load_genome():
    if os.path.exists(GENOME_FILE):
        with open(GENOME_FILE, "r") as f:
            return json.load(f)
    # Default initial population
    return [{
        "id": "generation_0",
        "genes": {a: random.random() for a in AGENTS},
        "fitness": 0.0 # Will be updated based on friction score
    }]

def calculate_friction():
    """Fitness function: fewer topics/outbox items = higher fitness (less friction)"""
    outbox = len(os.listdir(os.path.join(ROOT, "queues", "outbox"))) if os.path.exists(os.path.join(ROOT, "queues", "outbox")) else 0
    topics = len(os.listdir(os.path.join(ROOT, "topics"))) if os.path.exists(os.path.join(ROOT, "topics")) else 0
    return 1.0 / (1.0 + outbox + (topics * 0.1))

def mutate(genes):
    new_genes = genes.copy()
    # Randomly mutate one agent's routing weight
    target = random.choice(AGENTS)
    new_genes[target] = max(0.0, min(1.0, new_genes[target] + random.uniform(-0.2, 0.2)))
    return new_genes

def get_best_route(genome):
    best_specimen = max(genome, key=lambda x: x["fitness"])
    sorted_agents = sorted(best_specimen["genes"].items(), key=lambda x: x[1], reverse=True)
    return [a[0] for a in sorted_agents]

def main():
    genome = load_genome()
    
    # Evaluate current generation
    current_specimen = genome[-1]
    current_specimen["fitness"] = calculate_friction()
    
    print("="*60)
    print("GENETIC PIPELINE ROUTER")
    print("="*60)
    print(f"Current Generation: {len(genome)-1}")
    print(f"Fitness Score (1/Friction): {current_specimen['fitness']:.4f}")
    
    # Create next generation via mutation of the best
    best_specimen = max(genome, key=lambda x: x["fitness"])
    next_genes = mutate(best_specimen["genes"])
    
    genome.append({
        "id": f"generation_{len(genome)}",
        "genes": next_genes,
        "fitness": 0.0
    })
    
    # Keep only top 10 history to save space
    if len(genome) > 10:
        genome = sorted(genome, key=lambda x: x["fitness"], reverse=True)[:10]
        
    os.makedirs(os.path.dirname(GENOME_FILE), exist_ok=True)
    with open(GENOME_FILE, "w") as f:
        json.dump(genome, f, indent=2)
        
    print("\nNext Generation Routing Priority:")
    for i, agent in enumerate(get_best_route(genome), 1):
        print(f"{i}. {agent}")

if __name__ == "__main__":
    main()
