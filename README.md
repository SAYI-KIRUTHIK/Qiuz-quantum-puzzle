# 🧩 Quiz: A Quantum Puzzle Game

An interactive, gamified educational tool designed to introduce beginners and university students to the fundamentals of quantum mechanics and quantum circuit design. 

**Play it live here:** [Insert your Streamlit URL here once deployed]

## 📖 Pedagogical Goal
Bridging the gap between abstract linear algebra and practical quantum computing can be difficult. This application gamifies the learning process by translating complex quantum state manipulation into an intuitive puzzle format. 

Instead of passively reading about quantum logic, users must actively construct circuits to manipulate state vectors, leading to independent discovery of foundational concepts like superposition and quantum entanglement.

## ✨ Features
* **Interactive Circuit Builder:** Construct real quantum circuits using X (NOT), H (Hadamard), and CX (CNOT) gates.
* **Mathematical Validation:** The app runs accurate quantum simulations using IBM's Qiskit framework to generate and validate the resulting state vectors against target states.
* **Dynamic Visualization:** Circuits are rendered in real-time using Matplotlib, cleanly linking the visual gate layout to the mathematical output.
* **Progressive Difficulty:** Levels scale from simple 1-qubit bit-flips to a 2-qubit "Boss Level" where users must perfectly entangle a Bell State ($\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$).
* **Gamified Economy:** Solving puzzles rewards users with "Schrödinger Coins" (🐈‍⬛), which can be spent in the Knowledge Shop to unlock accessible explanations of real-world quantum phenomena like Quantum Teleportation.

## 🛠️ Technology Stack
* **Frontend/UI:** [Streamlit](https://streamlit.io/)
* **Quantum Logic Engine:** [Qiskit](https://qiskit.org/) (IBM)
* **Visual Rendering:** Matplotlib & NumPy

## 💻 How to Run Locally
If you want to run this project on your own machine:

1. Clone this repository.
2. Install the required dependencies: (in terminal)

   pip install -r requirements.txt
