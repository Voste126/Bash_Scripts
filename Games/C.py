#!/usr/bin/env python3
"""
security_quiz_game.py

A simple cybersecurity quiz game that:
- Asks multiple-choice questions
- Tracks correct and wrong answers
- Displays the final score
- Provides security tips on wrong answers
- Loops until user quits
"""
import datetime

# List of questions: each as dict with question, choices, correct answer, and tip
QUESTIONS = [
    {
        "question": "What makes a password strong?",
        "choices": {
            "a": "Using your birthday",
            "b": "At least 8 characters with numbers and symbols",
            "c": "Using 'password123'",
            "d": "Using your name"
        },
        "answer": "b",
        "tip": "Always include at least 8 characters combining letters, numbers, and symbols."
    },
    {
        "question": "What is a common sign of a phishing email?",
        "choices": {
            "a": "Unsolicited attachments or urgent requests",
            "b": "Email from your friend" ,
            "c": "Newsletter you subscribed to",
            "d": "Invoice from a known vendor"
        },
        "answer": "a",
        "tip": "Be cautious of emails with unexpected attachments or urgent requests for personal info."
    },
    {
        "question": "Why should you regularly update your software?",
        "choices": {
            "a": "To get new colors",
            "b": "To fix security vulnerabilities",
            "c": "To slow down your computer",
            "d": "To uninstall apps automatically"
        },
        "answer": "b",
        "tip": "Software updates often include security patches to protect against exploits."
    },
    {
        "question": "What is a safe practice for public Wi-Fi?",
        "choices": {
            "a": "Access banking websites without VPN",
            "b": "Use a VPN or avoid sensitive transactions",
            "c": "Share files with strangers",
            "d": "Disable firewall"
        },
        "answer": "b",
        "tip": "Use a VPN and avoid entering sensitive information on public networks."
    },
    {
        "question": "How can social engineering attacks succeed?",
        "choices": {
            "a": "By directly hacking password databases",
            "b": "By tricking users into revealing information",
            "c": "By using only strong encryption",
            "d": "By upgrading software"
        },
        "answer": "b",
        "tip": "Always verify identities and be cautious of unsolicited requests for info."
    }
]


def run_quiz():
    correct = 0
    wrong = 0
    total = len(QUESTIONS)

    print("=== Cybersecurity Quiz Game! ===")
    print("Type 'quit' at any prompt to exit")
    start_time = datetime.datetime.now()

    while True:
        for idx, q in enumerate(QUESTIONS, start=1):
            print(f"\nQuestion {idx}: {q['question']}")
            for key, choice in q['choices'].items():
                print(f"  {key}) {choice}")

            answer = input("Your answer (a/b/c/d): ").strip().lower()
            if answer == 'quit':
                show_summary(correct, wrong, start_time)
                return

            if answer == q['answer']:
                correct += 1
                print("Correct! 👍")
            else:
                wrong += 1
                print(f"Wrong! ❌ Tip: {q['tip']}")

            print(f"Score: {correct}/{correct + wrong}")

        # Loop finished all questions
        cont = input("\nContinue another round? (y/quit): ").strip().lower()
        if cont == 'quit':
            show_summary(correct, wrong, start_time)
            return
        # else reset or continue


def show_summary(correct, wrong, start_time):
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print("\n=== Quiz Summary ===")
    print(f"Total Questions Answered: {correct + wrong}")
    print(f"Correct: {correct}")
    print(f"Wrong: {wrong}")
    print(f"Time Taken: {duration}")
    print("Thank you for playing!")


if __name__ == '__main__':
    run_quiz()
