import streamlit as st
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

# --- 1. SETUP, MEMORY & SIDEBAR ---
st.set_page_config(page_title="Quantum_circuit_Puzzle", page_icon="🧩")

# Initialize our Game Economy Memory
if "coins" not in st.session_state:
    st.session_state.coins = 0
if "cleared_levels" not in st.session_state:
    st.session_state.cleared_levels = set() # Keeps track of beaten levels
if "unlocked_rewards" not in st.session_state:
    st.session_state.unlocked_rewards = set() # Keeps track of bought items
if "checked" not in st.session_state:
    st.session_state.checked = False

st.title("Qiuz: A Quantum Puzzle 🧩")

# Sidebar
st.sidebar.title("Game Status")
st.sidebar.metric(label="Schrödinger Coins", value=f"{st.session_state.coins} 🐈‍⬛")
st.sidebar.divider()

with st.sidebar.expander("💡 Need a Hint?"):
    with st.expander("X Gate (NOT)"):
        st.caption("Flips $|0\\rangle$ to $|1\\rangle$")
        st.caption("$|0\\rangle$ to $|1\\rangle$")
    with st.expander("Y Gate"):
        st.caption("Rotates around the Y-axis")
        st.caption("$|0\\rangle$ to $i|1\\rangle$")
    with st.expander("Z Gate"):
        st.caption("Rotates around the Z-axis")
        st.caption("$|0\\rangle$ to $|0\\rangle + i|1\\rangle$")
    with st.expander("H Gate (Hadamard)"):
        st.caption("Creates a 50/50 superposition")
        st.caption("$|0\\rangle$ to $|+\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle + |1\\rangle)$")
    with st.expander("CNOT Gate (2-qubit only)"):
        st.caption("Flips the target IF the control is $|1\\rangle$")
        st.caption("$|00\\rangle$ to $|00\\rangle$, $|01\\rangle$ to $|01\\rangle$, $|10\\rangle$ to $|11\\rangle$, $|11\\rangle$ to $|10\\rangle$")

# --- 2. DEFINE LEVELS (With Rewards Included!) ---
levels = {
    "Level 1: The Bit Flip": {
        "qubits": 1, 
        "target": Statevector([0.+0.j, 1.+0.j]), 
        "goal_text": "I want, $|1\\rangle$ or [0.+0.j, 1.+0.j]",
        "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]",
        "reward": 10
    },
    "Level 2: Superposition": {
        "qubits": 1, 
        "target": Statevector([1/np.sqrt(2), 1/np.sqrt(2)]), 
        "goal_text": "I want, $|+\\rangle$ or [1/np.sqrt(2), 1/np.sqrt(2)] (Equal superposition)",
        "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]",
        "reward": 10
    },
    "Level 3: Phase Shift": {
        "qubits": 1, 
        "target": Statevector([1/np.sqrt(2), -1/np.sqrt(2)]), 
        "goal_text": "I want, $|-\\rangle$ or [1/np.sqrt(2), -1/np.sqrt(2)] (Superposition with a negative phase)",
        "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]",
        "reward": 15
    },
    "Boss Level: Entanglement": {
        "qubits": 2, 
        "target": Statevector([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)]), 
        "goal_text": "I want, $\\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)$ or $\\frac{1}{\\sqrt{2}}[1, 0, 0, 1]$ (The Bell State)",
        "initial_state": "Qubit(s) with me, $|00\\rangle$ or [1, 0, 0, 0]",
        "reward": 25
    }
}

# UI Tabs: Split the app into a Game Area and a Shop Area
tab_play, tab_shop = st.tabs(["🎮 Play Puzzle", "🏪 Quantum Shop (Rewards)"])

# ==========================================
#               TAB 1: THE GAME
# ==========================================
with tab_play:
    level_name = st.selectbox("Choose a level:", list(levels.keys()))
    level_data = levels[level_name]
    num_qubits = level_data["qubits"]
    target_state = level_data["target"]
    level_reward = level_data["reward"]

    # Dynamic Circuit Management
    if "current_level" not in st.session_state or st.session_state.current_level != level_name or st.button("Reset Circuit 🔄"):
        st.session_state.current_level = level_name
        st.session_state.qc = QuantumCircuit(num_qubits)
        st.session_state.checked = False 

    qc = st.session_state.qc 

    # Game UI & Controls
    st.write(f"**Reward for clearing:** {level_reward} 🐈‍⬛")
    if level_name in st.session_state.cleared_levels:
        st.success("✅ You have already cleared this level!")


    st.write(f"### {level_name}")
    st.info(level_data["initial_state"])
    st.info(level_data["goal_text"])
    st.write("### Apply Your Gates:")


    if num_qubits == 1:
        with st.expander("Gates"):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("Apply X Gate"): qc.x(0)
            with col2:
                if st.button("Apply H Gate"): qc.h(0)
            with col3:
                if st.button("Apply Z Gate"): qc.z(0)
            with col4:
                if st.button("Apply Y Gate"): qc.y(0)
            #with col5:
            #   if st.button("Apply CCNot Gate"): qc.ccx(0, 1, 2) # This will do nothing since we only have 1 qubit, but it's fun to try!

    elif num_qubits == 2:
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.expander("Qubit(0) Controls"):
                if st.button("H Gate on q0"): qc.h(0)
                if st.button("X Gate on q0"): qc.x(0)
                if st.button("Z Gate on q0"): qc.z(0)
                if st.button("Y Gate on q0"): qc.y(0)
        with col2:
            with st.expander("Qubit(1) Controls"):
                if st.button("H Gate on q1"): qc.h(1)
                if st.button("X Gate on q1"): qc.x(1)
                if st.button("Z Gate on q1"): qc.z(1)
                if st.button("Y Gate on q1"): qc.y(1)
        with col3:
            with st.expander("Multi-Qubit Controls"):
                if st.button("CNOT (Control: q0, Target: q1)"): qc.cx(0, 1)
                if st.button("CNOT (Control: q1, Target: q0)"): qc.cx(1, 0)

    # Evaluation
    current_state = Statevector(qc)
    
    if st.button("Check Circuit ✅", type="primary"):
        st.session_state.checked = True

    st.write("### Your Current Circuit:")
    with st.container():
        fig = qc.draw(output='mpl', initial_state=True)
        st.pyplot(fig, use_container_width=False)

    if st.session_state.checked:
        if current_state.equiv(target_state):
            st.success("🎉 Puzzle Solved! Your state perfectly matches the target!")
            
            # Reward Logic: Only give coins if it's their first time beating it
            if level_name not in st.session_state.cleared_levels:
                st.session_state.cleared_levels.add(level_name)
                st.session_state.coins += level_reward
                st.balloons()
                st.toast(f"💰 You earned {level_reward} Schrödinger Coins! Go check the shop.")
            
            st.session_state.checked = False 
        else:
            st.error("❌ Not quite! Compare your Resulting Vector in the image above to the Target.")

st.warning("⚠️ Remember, measuring a quantum state collapses it!")

# ==========================================
#               TAB 2: THE SHOP
# ==========================================
with tab_shop:
    st.header("🏪 The Quantum Knowledge Shop")
    st.write("Spend your hard-earned Schrödinger Coins to unlock real-world quantum secrets!")
    st.metric(label="Available Balance", value=f"{st.session_state.coins} 🐈‍⬛")
    st.divider()

    # --- REWARD 1 ---
    st.subheader("🐈 Schrödinger's Cat (Thought Experiment)")
    if "cat" in st.session_state.unlocked_rewards:
        st.success("🔓 Unlocked!")
        st.write("""
        **The Concept:** Erwin Schrödinger proposed a scenario where a cat in a box is linked to a quantum event (like a decaying atom). 
        Because the atom is in a *superposition* of decayed and not-decayed, the cat is simultaneously dead and alive until you open the box to observe it!
        **Why it matters:** It highlights how bizarre quantum superposition is when applied to everyday, macroscopic objects.
        """)
    else:
        st.write("Cost: 20 🐈‍⬛")
        if st.button("Unlock Schrödinger's Cat", disabled=st.session_state.coins < 20):
            st.session_state.coins -= 20
            st.session_state.unlocked_rewards.add("cat")
            st.rerun() 

    st.divider()

    # --- REWARD 2 ---
    st.subheader("🛸 Quantum Teleportation (Real Tech)")
    if "teleport" in st.session_state.unlocked_rewards:
        st.success("🔓 Unlocked!")
        st.write("""
        **The Concept:** Scientists can't teleport physical matter (like in Star Trek), but using **Entanglement** (what you did in the Boss Level!), 
        they can instantly teleport the *information* of a quantum state from one location to another, even across the globe.
        **Why it matters:** This is the foundation of the ultra-secure "Quantum Internet" currently being built.
        """)
    else:
        st.write("Cost: 40 🐈‍⬛")
        if st.button("Unlock Quantum Teleportation", disabled=st.session_state.coins < 40):
            st.session_state.coins -= 40
            st.session_state.unlocked_rewards.add("teleport")
            st.rerun()