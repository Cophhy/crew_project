#!/usr/bin/env python
import sys
from content_creation_crew.crew import ContentCreationCrewCrew

def run():
    """
    Run the crew with a specific topic.
    """
    print("Welcome to the Content Creation Crew!")
    print("This crew will help you create comprehensive blog posts on any topic.")
    print()
    
    topic = input("Enter the topic you want to create content about: ")
    
    if not topic.strip():
        print("Please provide a valid topic.")
        return
    
    print(f"\nCreating content about: {topic}")
    print("This may take a few minutes as the agents collaborate...")
    print("-" * 50)
    
    inputs = {
        'topic': topic
    }
    
    try:
        result = ContentCreationCrewCrew().crew().kickoff(inputs=inputs)
        print("\n" + "="*50)
        print("FINAL RESULT:")
        print("="*50)
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure Ollama is running and the mistral model is available.")
        print("Try running: ollama list")
        print("If mistral is not listed, run: ollama pull mistral")

def train():
    """
    Train the crew for a given number of iterations.
    """
    topic = input("Enter the topic for training: ")
    
    inputs = {
        'topic': topic
    }
    try:
        ContentCreationCrewCrew().crew().train(n_iterations=int(sys.argv[1]), inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

if __name__ == "__main__":
    run()
