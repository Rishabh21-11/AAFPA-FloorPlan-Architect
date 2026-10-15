"""
Launcher script to train the AAFPA 2.0 Conversational Floor Plan Model.
"""

import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from aafpa.conversation_trainer import train_conversational_ai_model

if __name__ == "__main__":
    epochs = 10
    if len(sys.argv) > 1:
        try:
            epochs = int(sys.argv[1])
        except ValueError:
            pass
    train_conversational_ai_model(epochs=epochs)
