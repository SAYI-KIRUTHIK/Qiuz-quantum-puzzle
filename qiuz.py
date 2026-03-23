import os
import json
import io
import streamlit as st
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from supabase import create_client,Client
from qiskit.visualization import plot_histogram, plot_bloch_multivector
from qiskit_aer import AerSimulator
import time
import random

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))



# --- 1. SETUP, MEMORY & SIDEBAR ---
st.set_page_config(page_title="Quantum_circuit_Puzzle", page_icon="🧩",layout="wide")


# (Database connection logic will go here eventually)
# ==========================================
#        1. THE GATEKEEPER (LOGIN)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Center the login box nicely on the screen
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🧩 Qiuz: Login")      
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g., QuantumKid99")
            password = st.text_input("Password", type="password")
            
            c1, c2 = st.columns(2)
            with c1:
                btn_login = st.form_submit_button("Log In", use_container_width=True)
            with c2:
                btn_register = st.form_submit_button("Create Profile", use_container_width=True)
            
        # --- LOGIN LOGIC ---
        if btn_login:
            if username and password:
                # Ask Supabase if this user and password match
                response = supabase.table("profiles").select("*").eq("username", username).eq("password", password).execute()
                
                if len(response.data) > 0:
                    user_data = response.data[0]
                    # Success! Load their data into the session state
                    st.session_state.logged_in = True
                    st.session_state.username = user_data["username"]
                    st.session_state.coins = user_data["coins"]
                    st.session_state.cleared_levels = set() # We can save levels to the database later!
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password.")
            else:
                st.warning("Please enter both username and password.")
                
        # --- REGISTER LOGIC ---
        if btn_register:
            if username and password:
                # Check if someone already took this username
                check_user = supabase.table("profiles").select("*").eq("username", username).execute()
                
                if len(check_user.data) > 0:
                    st.error("⚠️ Username already taken. Please choose another one.")
                else:
                    # Insert the new user into the database with 0 coins
                    supabase.table("profiles").insert({"username": username, "password": password, "coins": 0}).execute()
                    st.success(f"✅ Profile '{username}' created! You can now log in.")
            else:
                st.warning("Please enter both username and password.")

# ==========================================
#        2. THE MAIN GAME
# ==========================================
else:
    # --- The User is Logged In! ---
    st.sidebar.title("Game Status")
    st.sidebar.success(f"👤 Playing as: {st.session_state.username}")    
    # The Log Out Button

    st.sidebar.metric(label="Catty-Coins", value=f"{st.session_state.coins} 🐈‍⬛")

    TOTAL_CHALLENGES = 11 
    cleared_count = len(st.session_state.cleared_levels)

    # Calculate percentage (and ensure it never breaks 100% if you add secret levels!)
    progress_pct = min(cleared_count / TOTAL_CHALLENGES, 1.0)
    st.sidebar.progress(
        progress_pct, 
        text=f"🏆 Campaign Progress: {cleared_count} / {TOTAL_CHALLENGES}"
    )
    if st.sidebar.button("Save & Log Out"):
        # Save their current coins to the database before they leave
        supabase.table("profiles").update({"coins": st.session_state.coins}).eq("username", st.session_state.username).execute()
        
        # Wipe the session state so the next person doesn't see their game
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()    
    st.sidebar.divider()


    # --- YOUR ENTIRE GAME CODE GOES HERE ---
    history_idx = 0
    if "unlocked_lore" not in st.session_state:
        st.session_state.unlocked_lore = [] # Tracks the names of purchased textbook pages
# Initialize our Game Economy Memory
    if "coins" not in st.session_state:
        st.session_state.coins = supabase.table("profiles").select("coins").eq("username", st.session_state.username).execute().data[0]["coins"]
    if "cleared_levels" not in st.session_state:
        st.session_state.cleared_levels = set() # Keeps track of beaten levels
    if "unlocked_rewards" not in st.session_state:
        st.session_state.unlocked_rewards = set() # Keeps track of bought items
    if "checked" not in st.session_state:
        st.session_state.checked = False
    if "history" not in st.session_state:
        st.session_state.history = []
    if "history_idx" not in st.session_state:
        st.session_state.history_idx = 0


    st.title("Qiuz: A Quantum Puzzle 🧩")
    st.divider()

    # Put all your game/challenge logic inside this scrollable container
    #with st.container(height=600, border=False):


    # Sidebar

        
    st.sidebar.subheader("Navigation")
    current_page = st.sidebar.radio("", ["🧘‍♀️ Sandbox Mode","📖 Interactive Tutorials","🎮 Play Challenge", "🏪 Quantum Shop", "📖 How to Play","🎲 symbols sheets","🌀 Readme-Gates"])




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


    with st.sidebar.expander("About"):
        st.write("### ⚙️ System Environment")
        st.write("- **Frontend UI:** Streamlit")
        st.write("- **Quantum Logic:** IBM Qiskit")
        st.write("- **Visual Rendering:** Matplotlib, NumPy, pylatexenc")
        st.divider()
        st.write("**Developed by:** SAKHI")
        st.write("**Contact:** sayikiruthikedu")
        st.write("**GitHub:** https://github.com/SAYI-KIRUTHIK/Qiuz-quantum-puzzle")


    # --- 2. DEFINE LEVELS (With Rewards Included!) ---
    if current_page == "📖 Interactive Tutorials":
        levels = {
            "Level 1: The Bit Flip (X)": {
                "qubits": 1, 
                "target": Statevector([0.+0.j, 1.+0.j]), 
                "goal_text": "I want, $|1\\rangle$ or [0.+0.j, 1.+0.j]",
                "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]",
                "reward": 10
            },
            "Level 2: The Cartwheel (Y)": {
                "qubits": 1, 
                "target": Statevector([0.+0.j, 0.+1.j]), 
                "reward": 15,
                "goal_text": "I want, $i|1\\rangle$ or [0.+0.j, 0.+1.j]",
                "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]"
                },
            "Level 3: The Superposition (H)": {
                "qubits": 1, 
                "target": Statevector([1/np.sqrt(2), 1/np.sqrt(2)]), 
                "goal_text": "I want, $|+\\rangle$ or $\\frac{1}{\\sqrt{2}}[1, 1]$ (Equal superposition)",
                "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]",
                "reward": 10
            },
            "Level 4: The Phase Shift (Z)": {
                "qubits": 1, 
                "target": Statevector([1/np.sqrt(2), -1/np.sqrt(2)]), 
                "goal_text": "I want, $|-\\rangle$ or $\\frac{1}{\\sqrt{2}}[1, -1]$ (Superposition with a negative phase)",
                "initial_state": "Qubit(s) with me, $|0\\rangle$ or [1.+0.j, 0.+0.j]",
                "reward": 15
            },    
            "Level 5: The Entanglement (CNOT)": {
                "qubits": 2, 
                "target": Statevector([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)]), 
                "goal_text": "I want, $\\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)$ or $\\frac{1}{\\sqrt{2}}$[1, 0, 0, 1] (The Bell State)",
                "initial_state": "Qubit(s) with me, $|00\\rangle$ or [1, 0, 0, 0]",
                "reward": 25
            },
            "Tutorial Boss: The Toffoli (CCNOT)": {
                "qubits": 3, 
                "target": Statevector([0, 0, 0, 0, 0, 0, 0, 1]),
                "goal_text": "I want, $|111\\rangle$ or [0, 0, 0, 0, 0, 0, 0, 1] (The Toffoli State)",
                "initial_state": "Qubit(s) with me, $|000\\rangle$ or [1, 0, 0, 0, 0, 0, 0, 0]", 
                "reward": 50}     # Target is |111>
        }

        # --- CAMPAIGN PROGRESSION LOGIC ---
        # This checks what the user has beaten and only reveals the next level
        available_levels = ["Level 1: The Bit Flip (X)"]
        if "Level 1: The Bit Flip (X)" in st.session_state.cleared_levels: available_levels.append("Level 2: The Cartwheel (Y)")
        if "Level 2: The Cartwheel (Y)" in st.session_state.cleared_levels: available_levels.append("Level 3: The Superposition (H)")
        if "Level 3: The Superposition (H)" in st.session_state.cleared_levels: available_levels.append("Level 4: The Phase Shift (Z)")
        if "Level 4: The Phase Shift (Z)" in st.session_state.cleared_levels: available_levels.append("Level 5: The Entanglement (CNOT)")
        if "Level 5: The Entanglement (CNOT)" in st.session_state.cleared_levels: available_levels.append("Tutorial Boss: The Toffoli (CCNOT)")

    # UI Tabs: Split the app into a Game Area and a Shop Area
    # Add this to your sidebar section



    # ==========================================
    #               TAB 1: THE GAME
    # ==========================================

        level_name = st.selectbox("Choose a level:", available_levels)
        level_data = levels[level_name]
        num_qubits = level_data["qubits"]
        target_state = level_data["target"]
        level_reward = level_data["reward"]

        # Dynamic Circuit Management
        if "current_level" not in st.session_state or st.session_state.current_level != level_name:
            st.session_state.current_level = level_name
            st.session_state.qc = QuantumCircuit(num_qubits)
            st.session_state.checked = False 

        qc = st.session_state.qc 

        # Game UI & Controls
        st.write(f"**Reward for clearing:** {level_reward} 🐈‍⬛")
        if level_name in st.session_state.cleared_levels:
            st.success("✅ You have already cleared this level!")


        st.write(f"### {level_name}")
        st.info(level_data["initial_state"] + "\n" + " and " + level_data["goal_text"], icon="ℹ️")
        col_main,col_gates = st.columns([8,3])
        with col_gates:        # --- THE CIRCUIT VISUALIZER ---
                with st.container(border=True):

                        st.write("### Apply Your Gates:")
                
                # This loop automatically builds a row for however many qubits the challenge has!
                        for i in range(num_qubits):
                            st.markdown(f"**Qubit {i}**")
                    
                    # Create 4 tiny columns just for the buttons on this specific row
                            g1, g2, g3, g4 = st.columns(4)
                    
                            with g1:
                                if st.button("X", key=f"x{i}", use_container_width=True): qc.x(i)
                            with g2:
                                if st.button("Y", key=f"y{i}", use_container_width=True): qc.y(i)
                            with g3:
                                if st.button("Z", key=f"z{i}", use_container_width=True): qc.z(i)
                            with g4:
                                if st.button("H", key=f"h{i}", use_container_width=True): qc.h(i)
                        
                            st.divider() # Adds a neat line between qubits
                    
                # Multi-Qubit Gates (Placed at the very bottom, taking up the full width)
                        if num_qubits > 1:
                            st.markdown("**Two-Qubit Gates**")
                            if st.button("CNOT (Ctrl: q0, Targ: q1)", key="cx01", use_container_width=True): qc.cx(0, 1)
                            if st.button("CNOT (Ctrl: q1, Targ: q0)", key="cx10", use_container_width=True): qc.cx(1, 0) 
                        if num_qubits > 2:
                            st.markdown("**Three-Qubit Gates**")
                            if st.button("Toffoli (Ctrl: q0,q1, Targ: q2)", key="ccx012", use_container_width=True): qc.ccx(0, 1, 2)   
                            if st.button("Toffoli (Ctrl: q0,q2, Targ: q1)", key="ccx021", use_container_width=True): qc.ccx(0, 2, 1)
                            if st.button("Toffoli (Ctrl: q1,q2, Targ: q0)", key="ccx120", use_container_width=True): qc.ccx(1, 2, 0)

        # Evaluation
        current_state = Statevector(qc)


        with col_main:    
            st.write("### Your Current Circuit:")
            with st.container():
                fig = qc.draw(output='mpl', initial_state=True)
                st.pyplot(fig, use_container_width=False)


            col_check,col_reset = st.columns([2,2]) 

            with col_check:
                if st.button("Check Circuit", type="primary", use_container_width=True):
                    st.session_state.checked = True
                    st.write("### 🔍 Results")
                    st.write("**Your Resulting State Vector:**")
                    st.code(np.round(current_state.data, 3))

            with col_reset:
                # This button will now sit right next to the Check button
                if st.button("Reset", use_container_width=True):
                    st.session_state.qc = QuantumCircuit(num_qubits)
                    st.session_state.checked = False
                    st.rerun()
                
            if st.session_state.checked:
                if current_state.equiv(target_state):
                    st.success("🎉 Thanks, I got my state! and you got your catty-coin!")
                    st.balloons()
                    #st.toast(f"💰 You earned {level_reward} Catty-Coins! Check the textbook for your new unlock.")
                # Fun visual reward
                    
                    # Reward Logic: Only give coins if it's their first time beating it
                    if level_name not in st.session_state.cleared_levels:
                        st.session_state.cleared_levels.add(level_name)
                        st.session_state.coins += level_reward
                        st.toast(f"💰 You earned {level_reward} Catty-Coins! Check the textbook for your new unlock.")
                        st.rerun() # Forces a refresh to instantly update the dropdown and textbook
                    st.session_state.checked = False
                    
                else:
                    st.error("❌ This is not my target state. Can you try again?")
        st.warning("⚠️ Remember, measuring a quantum state collapses it!")


    # ==========================================
    #               PAGE 2: THE SHOP
    # ==========================================
    if current_page == "🏪 Quantum Shop":
        st.header("🏪 The Quantum Shop")
        st.write("Every loves lore, here take some good ones in  exchange of catty-coins 🐈‍⬛")
        
        # --- 1. THE LORE DATABASE ---
        lore_db = {
            "Superposition": {
                "cost": 15, 
                "icon": "🌊",
                "text": "In classical mechanics, a coin is either heads or tails. In quantum mechanics, a qubit can exist in a linear combination of both states simultaneously until measured. Mathematically, this is represented as $|\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$."
            },
            "Entanglement": {
                "cost": 30, 
                "icon": "🔗",
                "text": "Einstein called it 'spooky action at a distance.' When two qubits become entangled (often via a CNOT gate), their physical states become permanently linked. Measuring one instantly collapses the state of the other, no matter how far apart they are."
            },
            "Phase Kickback": {
                "cost": 50, 
                "icon": "🪃",
                "text": "A clever quantum trick where applying a controlled gate (like a CNOT) to a target qubit that is in the $|-\\rangle$ state actually 'kicks' a negative phase back onto the *control* qubit, without altering the target qubit's probabilities!"
            },
            "Schrödinger's Cat": {
                "cost": 100, 
                "icon": "🐈‍⬛",
                "text": "A famous thought experiment by Erwin Schrödinger. If you place a cat in a sealed box with a quantum-triggered vial of poison, the cat is theoretically considered both alive and dead simultaneously until you open the box to observe (measure) it."
            }
        }
        
        # --- 2. THE BUY FUNCTION ---
        def buy_lore(item_name, cost):
            if st.session_state.coins >= cost:
                st.session_state.coins -= cost
                st.session_state.unlocked_lore.append(item_name)
                st.toast(f"Successfully purchased: {item_name}!", icon="🎉")
            else:
                st.toast("Not enough Catty-Coins!", icon="❌")

        st.divider()
        
        # --- 3. THE UI: SHOP vs LIBRARY ---
        tab_shop, tab_library = st.tabs(["🛒", "📖 Library"])
        
        # THE SHOP TAB
        with tab_shop:
            st.write(f"### Current Balance: **{st.session_state.coins}** 🐈‍⬛")
            
            # Create a grid of 2 columns for the shop items
            col1, col2 = st.columns(2)
            
            # Loop through our database and draw a "card" for each item
            for idx, (item_name, details) in enumerate(lore_db.items()):
                # Alternate columns so it looks like a nice grid
                target_col = col1 if idx % 2 == 0 else col2
                
                with target_col:
                    with st.container(border=True):
                        st.write(f"#### {details['icon']} {item_name}")
                        
                        if item_name in st.session_state.unlocked_lore:
                            st.success("✅ Already Unlocked")
                            # Disabled button
                            st.button("Purchased", key=f"buy_{item_name}", disabled=True, use_container_width=True)
                        else:
                            st.write(f"**Cost:** {details['cost']} Catty-Coins")
                            # The Buy button!
                            st.button(f"Buy {item_name}", key=f"buy_{item_name}", on_click=buy_lore, args=(item_name, details['cost']), use_container_width=True, type="primary")

        # THE LIBRARY TAB
        with tab_library:
            st.write("### From the GREATS!")
            if len(st.session_state.unlocked_lore) == 0:
                st.info("Your library is empty! Go beat some challenges to earn coins and buy textbook pages.")
            else:
                # Draw a beautiful reading expanding box for every unlocked item
                for unlocked_item in st.session_state.unlocked_lore:
                    details = lore_db[unlocked_item]
                    with st.expander(f"{details['icon']} **{unlocked_item}**", expanded=True):
                        st.write(details['text'])

    # ==========================================
    #               PAGE 3 : TUTORIAL
    # ==========================================

    if current_page == "📖 How to Play":
        st.header("📖 How to Play: A Beginner's Guide")
        st.write("Welcome to Qiuz! (ki-sz) If you are new to quantum mechanics, don't worry. This guide will show you exactly how to operate the game.")
        
        st.divider()

        st.subheader("1. The Sidebar & Hint")
        st.write("On the left side of your screen, you will see your **Game Status**. This tracks how many Catty-Coins (🐈‍⬛) you have earned. Below that is a **Hint** optionthat explains what each quantum gate does in a very brief way.")
        sidebar_img = os.path.join(BASE_DIR, "assets", "sidebar.png")
        if os.path.exists(sidebar_img): 
            st.image(sidebar_img)
        else:
            st.error(f"Could not find image at: {sidebar_img}")

        st.subheader("2. Applying Quantum Gates")
        st.write("Choose a level from the dropdown menu. Your goal is to apply gates to the starting state (usually $|0\\rangle$) to match the Target State, which you can find below the drop-down menu. Click the buttons to add gates to your circuit wire.")
        gates_img = os.path.join(BASE_DIR, "assets", "gates.png")
        if os.path.exists(gates_img):
            st.image(gates_img)
        else:
            st.error(f"Could not find image at: {gates_img}")

        st.subheader("3. Checking Your Answer")
        st.write("As you click gates, the visual circuit updates automatically and you can see your resulting state vector, below the circuit drawing. When you think you have solved it, click the red **Check Circuit ✅** button. The app will calculate the complex math and display your resulting state vector directly below the circuit drawing as mentioned previously.")
        check_img = os.path.join(BASE_DIR, "assets", "check.png")
        if os.path.exists(check_img):
            st.image(check_img)
        else:
            st.error(f"Could not find image at: {check_img}")

        st.subheader("4. Resetting Your Circuit")
        st.write("If you want to start over with your circuit, simply click the **Reset Circuit** button from the bottom of the sidebar. This will clear all applied gates and return you to the initial state.")
        reset_img = os.path.join(BASE_DIR, "assets", "reset.png")
        if os.path.exists(reset_img):
            st.image(reset_img)
        else:
            st.error(f"Could not find image at: {reset_img}")

        st.subheader("5. Understanding the Gates")
        st.write("If you are confused about what the gates do, simply click on the **Readme-Gates** tab from sidebar to get a thorough understanding of what each gate does to a qubit state. You can unlock this information by clearing the level, or you can have a quick peek at the hints in the sidebar, but the Readme-Gates tab will give you a much more detailed explanation of how each gate manipulates quantum states.")
        readme_img = os.path.join(BASE_DIR, "assets", "readme.png")
        if os.path.exists(readme_img):
            st.image(readme_img)
        else:
            st.error(f"Could not find image at: {readme_img}")


        st.subheader("6. The Quantum Shop")
        st.write("Once you successfully clear a level, you earn catty-coins! Navigate to the **Quantum Shop** tab at the top of the screen to spend your coins on unlocking real-world quantum physics secrets and much more in the future.")
        shop_img = os.path.join(BASE_DIR, "assets", "shop.png")
        if os.path.exists(shop_img):
            st.image(shop_img)
        else:
            st.error(f"Could not find image at: {shop_img}")

        st.success("🎉 You are ready to play! Head back to the 'Play Puzzle' tab to begin.")

    # ==========================================
    #               PAGE 4 : GATES
    # ==========================================

    if current_page == "🌀 Readme-Gates":
        st.header("🌀 Quantum Gates")
        st.write("Before we build circuits, we need to understand what we are actually building them with.")
        
        st.subheader("What is a Qubit?")
        
        tab_beginner, tab_advanced = st.tabs(["🟢 Start Here", "🔴 The Math"])
        
        with tab_beginner:
            st.info("""
            **The Classical Bit:** Think of a normal computer bit like a light switch. It is either completely OFF (0) or completely ON (1). 
            
            **The Qubit:** A quantum bit is like a spinning coin. While it spins, it isn't just Heads (0) or Tails (1); it is a blurry combination of both at the same time! We call this **Superposition**. However, the moment you slap your hand down to look at it (Measurement), it collapses back into a normal 0 or 1.
            """)

        with tab_advanced:
            st.write("**The Hilbert Space**")
            st.write("A qubit is described by a state vector $|\psi\\rangle$ in a 2D complex Hilbert space, represented as a linear combination of basis states:")
            st.latex(r"|\psi\rangle = \alpha|0\rangle + \beta|1\rangle")
            st.write("Here, $\\alpha$ and $\\beta$ are complex probability amplitudes where the sum of their absolute squares must equal $1$:")
            st.latex(r"|\alpha|^2 + |\beta|^2 = 1")
            st.write("Unlike classical bits confined to the poles of a sphere, a qubit can be manipulated to point anywhere on the surface of a Bloch Sphere using Unitary matrices.")

        # --- 2. THE LANGUAGE OF QUANTUM ---
        st.subheader("🧮 The Language: Symbols & Vectors")
        tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])
        
        with tab_beginner:
            st.info("""
            **The "Ket" Symbol**
            In normal math, if we want to talk about the number zero, we just write `0`. But in quantum mechanics, we want to make it obvious that we are talking about a *quantum state* (our spinning coin), not just a boring number. 
            
            To do this, physicists put the number inside a special bracket that looks like this: $| \\rangle$. This is called a **"Ket"**.
            
            * **$|0\\rangle$** (Pronounced "Ket-Zero"): This is our coin sitting flat on the table showing Heads.
            * **$|1\\rangle$** (Pronounced "Ket-One"): This is our coin sitting flat on the table showing Tails.
            
            Whenever you see this bracket, just know that it's a quantum state!
            """)
        with tab_advanced:
            st.write("**The Computational Basis**")
            st.write("To actually do math with quantum gates, we have to translate those 'Ket' symbols into Linear Algebra. Quantum states are represented as **column vectors**.")
            st.write("The states $|0\\rangle$ and $|1\\rangle$ form the standard computational basis. They are defined as orthogonal vectors:")
            
            # Using columns to put the math side-by-side cleanly
            col_math1, col_math2 = st.columns(2)
            with col_math1:
                st.latex(r"|0\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}")
            with col_math2:
                st.latex(r"|1\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}")
                
            st.write("**Building the State Vector:**")
            st.write("Because of this, a full state in superposition ($|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$) translates perfectly into a single matrix:")
            st.latex(r"|\psi\rangle = \begin{pmatrix} \alpha \\ \beta \end{pmatrix}")
            st.write("The top row tracks the amplitude for $|0\\rangle$, and the bottom row tracks the amplitude for $|1\\rangle$. Quantum gates are simply $2 \\times 2$ matrices that multiply against this column vector!")

        st.divider()
        


    # --- 2. PAULI-X GATE ---
        st.subheader("❌ The Pauli-X Gate (Quantum NOT)")
        tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])
        
        with tab_beginner:
            st.info("""
            **What does it do?**
            The Pauli-X gate is the quantum version of a classic "NOT" switch. Think of a coin sitting on a table showing Heads ($|0\\rangle$). If you apply an X gate, you simply flip the coin over so it shows Tails ($|1\\rangle$).
            """)
        with tab_advanced:
            st.write("**Matrix Representation:**")
            st.latex(r"X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}")
            st.write("**Dirac Notation:**")
            st.latex(r"X = |0\rangle\langle 1| + |1\rangle\langle 0|")
            st.write("**Core Properties:**")
            st.write("* **Hermitian & Unitary:** $X = X^\dagger$ and $X^2 = I$.")
            st.write("* **Bloch Sphere:** Represents a $\pi$ radian rotation around the x-axis.")

        st.divider()

        # --- 3. PAULI-Y GATE ---
        st.subheader("🧭 The Pauli-Y Gate")
        if "Level 1: The Bit Flip (X)" in st.session_state.cleared_levels:
            tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])

            with tab_beginner:
                st.info("""
                **The Gymnastics Analogy: Front Flips vs. Cartwheels**
                
                To understand the Y-Gate, imagine you are standing on your feet (Heads or $|0\\rangle$) and your goal is to end up in a handstand (Tails or $|1\\rangle$). 
                
                * **The X-Gate is a Front Flip:** You flip straight forward and land on your hands. You are upside down, and you are still facing forward.
                * **The Y-Gate is a Cartwheel:** You flip sideways. You still land on your hands, but because of the sideways rotation, you end up facing $90^\\circ$ to the left!
                
                **What is Quantum Phase?**
                That new direction you are facing is called the **Phase** (written mathematically as the imaginary number $i$). 
                
                If we only care whether you are on your feet or your hands (Heads or Tails), the X and Y gates do the exact same thing. But, if you need to catch another gymnast while upside down, the direction you are facing matters immensely! The Y-Gate flips the coin, but twists the direction it "faces" in the quantum world, changing how it interacts with other coins later in the game.
                """)
                
            with tab_advanced:
                st.write("**Matrix Representation:**")
                st.write("The Pauli-Y matrix introduces complex numbers into our gate operations:")
                st.latex(r"Y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}")
                
                st.write("**Dirac Notation:**")
                st.latex(r"Y = i|1\rangle\langle 0| - i|0\rangle\langle 1|")
                
                st.write("**Core Properties:**")
                st.write("* **Hermitian & Unitary:** $Y = Y^\dagger$ and $Y^2 = I$.")
                st.write("* **Bloch Sphere:** Represents a $\pi$ radian ($180^\circ$) rotation around the y-axis. It perfectly maps $|0\\rangle \to i|1\\rangle$ and $|1\\rangle \to -i|0\\rangle$.")
                st.write("* **The Pauli Group Identity:** $Y$ can be constructed by combining the X and Z gates with a global phase: $Y = iXZ$.")
        else:
            st.warning("🔒 **LOCKED:** Clear 'Level 1' to unlock the Y-Gate!")
            


        st.divider()

        # --- 3. HADAMARD GATE ---
        st.subheader("🔀 The Hadamard Gate (H)")

        if  "Level 2: The Cartwheel (Y)" in st.session_state.cleared_levels:

            tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])    
            with tab_beginner:
                    st.info("""
                    **What does it do?**
                    This is the most famous gate in quantum computing. If the X-Gate flips the coin over, the Hadamard gate is the finger that **flicks the coin to make it spin.** **The Rules:**
                    * When you apply an H-Gate to a resting coin ($|0\\rangle$ or $|1\\rangle$), it puts it into a perfect 50/50 **Superposition**. 
                    * If you measure it now, you have a completely random, 50% chance of getting Heads and 50% chance of getting Tails.
                    * **The Quantum Magic:** If you apply an H-Gate to a coin that is *already* spinning, it instantly stops it and lands it perfectly flat! (Applying it twice undoes the spin).
                    """)
            with tab_advanced:
                    st.write("**Matrix Representation:**")
                    st.write("The Hadamard gate creates an equal superposition. It is represented by the matrix:")
                    st.latex(r"H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}")
                    
                    st.write("**Dirac Notation (Action on Basis States):**")
                    st.write("It maps the computational basis states to the diagonal basis states ($|+\\rangle$ and $|-\\rangle$):")
                    st.latex(r"H|0\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle) = |+\rangle")
                    st.latex(r"H|1\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle) = |-\rangle")
                    
                    st.write("**Core Properties:**")
                    st.write("* **Hermitian & Unitary:** Like the Pauli matrices, $H = H^\dagger$ and $H^2 = I$. This is why applying it twice returns the qubit to its original state.")
                    st.write("* **Bloch Sphere:** It represents a rotation of $\pi$ about the axis $(x+z)/\sqrt{2}$. Geometrically, it reflects the state across the diagonal line halfway between the x and z axes.")
        else:
            st.warning("🔒 **LOCKED:** Clear 'Level 2' to unlock the Hadamard Gate!")

        st.divider()

        # --- 4. PAULI-Z GATE ---
        st.subheader("⏱️ The Pauli-Z Gate (Phase Flip)")
        if "Level 3: The Superposition (H)" in st.session_state.cleared_levels:
            tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])
            with tab_beginner:
                st.info("""
                **What does it do?**
                The Z-Gate is the "Phase" gate. If you apply a Z-gate to a coin sitting on the table, **absolutely nothing happens.** Heads stays Heads, and Tails stays Tails. 
                
                *So what is the point?*
                
                The Z-Gate only shows its power when the coin is *spinning* (in a Superposition). If the coin is spinning clockwise, the Z-Gate instantly reverses it to spin counter-clockwise! 
                
                It doesn't change your 50/50 chances of getting Heads or Tails when you finally slap your hand down, but reversing that spin is a crucial trick used in almost every advanced quantum algorithm.
                """)
            with tab_advanced:
                st.write("**Matrix Representation:**")
                st.write("The Pauli-Z gate leaves the $|0\\rangle$ amplitude alone, but flips the sign of the $|1\\rangle$ amplitude:")
                st.latex(r"Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}")
                
                st.write("**Dirac Notation:**")
                st.latex(r"Z = |0\rangle\langle 0| - |1\rangle\langle 1|")
                
                st.write("**Core Properties:**")
                st.write("* **Bloch Sphere:** Represents a $\pi$ radian rotation around the z-axis (the vertical pole of the sphere).")
                st.write("* **Phase Flip:** If a qubit is in the $|+\\rangle$ superposition state, the Z-gate flips it to the $|-\\rangle$ state, effectively changing its relative phase by $180^\circ$ without altering its measurement probabilities in the computational basis.")
                st.latex(r"Z|+\rangle = |-\rangle")
        else:
            st.warning("🔒 **LOCKED:** Clear 'Level 3' to unlock the Z-Gate!")        

        st.divider()



        # --- 4. CNOT GATE ---
        st.subheader("🔗 The CNOT (CX) Gate & Entanglement")

        if "Level 4: The Phase Shift (Z)" in st.session_state.cleared_levels:
            tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])
        
        
            with tab_beginner:
                st.info("""
                **What is Control and Target?**
                The CNOT gate connects two coins together. To understand how, think of a **motion-activated lightbulb**. 
                * **The Control (The Sensor):** This coin just watches. Its own state never changes during the operation.
                * **The Target (The Bulb):** This is the coin that gets acted upon.
                
                **The Rule:** If the Control coin is Heads ($0$), the sensor sees nothing, and the Target coin is left completely alone. If the Control coin is Tails ($1$), the sensor triggers, and it completely flips the Target coin over!
                """)
                
            with tab_advanced:
                st.write("**The Mathematical Definition of Control/Target:**")
                st.write("Let the state of a 2-qubit system be defined as $|c, t\\rangle$, where $c$ is the Control qubit and $t$ is the Target qubit. The CNOT gate performs modulo 2 addition (an XOR operation) on the target, leaving the control unchanged:")
                st.latex(r"CX|c, t \rangle = |c, c \oplus t \rangle")
                
                st.write("**Matrix Representation (4D Hilbert Space):**")
                st.write("Operating on the basis states $\{|00 \\rangle, |01\\rangle, |10\\rangle, |11\\rangle\}$, the matrix is:")
                st.latex(r"CX = \begin{pmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{pmatrix}")
        else:
            st.warning("🔒 **LOCKED:** Clear 'Level 4' to unlock the CNOT Gate!")    
        st.divider()

        # --- 5. CCNOT GATE ---
        st.subheader("🚦 The Toffoli (CCNOT) Gate: The Classical Bridge")

        if "Level 5: The Entanglement (CNOT)" in st.session_state.cleared_levels:    
            tab_beginner, tab_advanced = st.tabs(["🟢 Beginner", "🔴 Advanced"])
            
            with tab_beginner:
                st.info("""
                **The Two-Key System**
                If the CNOT gate is a motion sensor, the CCNOT (Controlled-Controlled-NOT) gate is like a nuclear launch console that requires **two** keys to be turned at the exact same time.
                
                It uses 3 coins: Two **Controls** and one **Target**.
                * **The Rule:** It only flips the Target coin IF Control #1 **AND** Control #2 are both Tails ($1$). If either control is Heads ($0$), the target is left alone.
                
                **Is this the Universal Gate?**
                Yes and no! 
                * **Classical Universality:** The Toffoli gate is the quantum version of the famous **NAND** gate. Because it is reversible, it allows a quantum computer to simulate any classical computer program perfectly. 
                * **Quantum Universality:** To simulate the universe, you need superposition. If you pair the Toffoli gate with our coin-spinning friend, the **Hadamard (H) Gate**, you achieve full **Quantum Universality**. With just Toffoli and Hadamard, you can calculate anything the universe allows!
                """)
                
            with tab_advanced:
                st.write("**Reversible Computing & Landauer's Principle**")
                st.write("Classical logic gates like AND/NAND are irreversible (they map 2 bits to 1 bit, destroying information and generating heat). Quantum mechanics requires unitary, reversible operations. The Toffoli gate achieves classical universality reversibly by using 3 qubits.")
                
                st.write("**The Mathematical Definition:**")
                st.write("Operating on three qubits $|c_1, c_2, t\\rangle$, the Toffoli gate applies a Pauli-X to the target only if both controls are $|1\\rangle$. This is equivalent to mapping the target to the XOR of itself and the AND of the controls:")
                st.latex(r"CCNOT|c_1, c_2, t\rangle = |c_1, c_2, t \oplus (c_1 \land c_2)\rangle")
                
                st.write("**Matrix Representation (8D Hilbert Space):**")
                st.write("Because it operates on 3 qubits, it is represented by an $8 \\times 8$ identity matrix, where the bottom right $2 \\times 2$ block is a Pauli-X gate:")
                st.latex(r"""
                CCNOT = \begin{pmatrix} 
                1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\
                0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
                0 & 0 & 0 & 0 & 0 & 0 & 0 & 1 \\
                0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 
                \end{pmatrix}
                """)
                
                st.write("**Shi's Theorem (Quantum Universality):**")
                st.write("While Toffoli is universal for reversible boolean logic, Shi's Theorem formally proves that the set consisting of the Toffoli gate and the Hadamard gate is universal for quantum computation.")
        else:
            st.warning("🔒 **LOCKED:** ' Level 5' to unlock the Toffoli Gate!")
        st.divider()

    if current_page == "🎲 symbols sheets":
        st.subheader("🎲 Quantum Symbols Chart Sheet")
        st.write("Use this lookup table to translate quantum symbols back into classical digital logic.")

        st.markdown("""
        | Symbol | How to Read It | Classical / Digital Equivalent | Quantum Meaning & Function |
        | :--- | :--- | :--- | :--- |
        | $0$ or $1$ | "Zero" or "One" | **Bit** (Standard ON/OFF logic state) | *Not used.* Quantum mechanics requires the "Ket" notation. |
        | $\\vert0\\rangle$ | "Ket-Zero" | **Bit = 0** (OFF / False) | The baseline quantum state. A coin resting flat on Heads. |
        | $\\vert1\\rangle$ | "Ket-One" | **Bit = 1** (ON / True) | The flipped quantum state. A coin resting flat on Tails. |
        | $\\vert+\\rangle$ | "Ket-Plus" | *None* | **Superposition**. The coin is spinning. An equal blend of 0 and 1. |
        | $\\alpha$ , $\\beta$ | "Alpha" , "Beta" | **Probability** | **Probability Amplitudes**. Complex numbers dictating the state. |
        | $X$ | "Pauli-X Gate" | **NOT Gate** (Inverter) | Flips $\\vert0\\rangle$ to $\\vert1\\rangle$ and vice-versa. |
        | $Y$ | "Pauli-Y Gate" | *None* | Flips $\\vert 0 \\rangle$ and $\\vert 1 \\rangle$ but adds an imaginary phase ($i$). |
        | $Z$ | "Pauli-Z Gate" | *None* | Does nothing to $\\vert 0 \\rangle$. Flips the phase/sign of $\\vert 1 \\rangle$. |   
        | $H$ | "Hadamard Gate" | *None* | Puts a resting qubit into a perfect superposition. |
        | $CX$ | "C-NOT" | **XOR Gate** | Flips Target if Control is $\\vert1\\rangle$. Creates Entanglement. |
        | $CCNOT$ | "Toffoli Gate" | **NAND / AND Gate** | Flips Target if Control 1 AND Control 2 are $\\vert1\\rangle$. |
        | $\\oplus$ | "O-Plus" (XOR) | **Modulo-2 Addition** | Math symbol for the XOR logic inside CNOT/Toffoli. |
        | $\\otimes$ | "Tensor Product"| **Parallel Bus / Wires** | Math used to combine independent qubits into one system. |
        """)
        st.divider()

    # ==========================================
    #                GAME
    # ==========================================
    if current_page == "🎮 Play Challenge": #GWHxbbP5wFePgo9s

            st.header("🎯 The Challenge Mode")
                
                # 1. THE TEXTBOOK DATA REGISTRY
                # This stores all the physics constants and targets in one clean spot
            challenges = {
                    "Challenge A": {
                        "qubits": 1,
                        "target": [1/np.sqrt(2), 1/np.sqrt(2)],
                        "initial_state": "$|0\\rangle$",
                        "goal_text": "Create the $|+\\rangle$ state (Equal Superposition)",
                        "output": " $\\frac{1}{\\sqrt{2}}|0\\rangle + \\frac{1}{\\sqrt{2}}|1\\rangle$",
                        "reward": 20,
                        "reference": ""
                    },
                    "Challenge B": {
                        "qubits": 2,
                        "target": [1/np.sqrt(2), 0, 0, 1/np.sqrt(2)],
                        "initial_state": " $|00\\rangle$",
                        "goal_text": "Create the $|\\Phi^+\\rangle$ entangled state",
                        "output": "$\\frac{1}{\\sqrt{2}}|00\\rangle + \\frac{1}{\\sqrt{2}}|11\\rangle$",
                        "reward": 25,
                        "reference": "*Quantum Computation* (McMahon), Chapter 8."
                    },
                    "Challenge C": {
                        "qubits": 2,
                        "target": [0, 1/np.sqrt(2), 0, -1/np.sqrt(2)],
                        "initial_state": "$|01\\rangle$",
                        "goal_text": "Use a CNOT to flip the phase of the Control qubit",
                        "output": "$\\frac{1}{\\sqrt{2}}|01\\rangle - \\frac{1}{\\sqrt{2}}|11\\rangle$",
                        "reward": 30,
                        "reference": ""
                    },
                    "Challenge D: The Imaginary Spin": {
                        "qubits": 1,
                        "target": [0, 1j], # 0 probability of |0>, 100% probability of |1> but with an imaginary phase
                        "initial_state": "Initial State: $|0\\rangle$",
                        "goal_text": "Objective: Create the state $i|1\\rangle$. Hint: Think about cartwheels.",
                        "output": "$i|1\\rangle$",
                        "reference": "",
                        "reward": 15
                    },
                    "Challenge E: The Un-Entangler": {
                        "qubits": 2,
                        "target": [1, 0, 0, 0], # Pure |00> state
                        "initial_state": "Initial State: $\\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)$ (Bell State)",
                        "goal_text": "Objective: Destroy the entanglement and return to $|00\\rangle$.",
                        "output": "$|00\\rangle$",
                        "reference": "",
                        "reward": 40
                    },
                    "Challenge F: The Quantum Swap": {
                        "qubits": 2,
                        "target": [0, 0, 1, 0], # The |10> state
                        "initial_state": "Initial State: $|01\\rangle$",
                        "goal_text": "Objective: Swap the states of the qubits using ONLY CNOT gates.",
                        "output": "$|10\\rangle$",
                        "reference": "",
                        "reward": 50
                    }
                }
            with st.popover("Objective Menu", use_container_width=True):
                st.write("These challenges are adapted from various textbooks on *Quantum Computation and Circuit Design* by various authors. The examples can added from the suggestions from local communities. The goal is to give players a taste of the classic textbook exercises, but in a more interactive way. Each challenge has a specific target state that you must create using the quantum gates at your disposal. If you can match the target state, you win the challenge.")
                ch_choice = st.radio("Objectives", list(challenges.keys()), horizontal=True, label_visibility="collapsed")
                # --- INITIALIZE CHALLENGE CONSTRAINTS ---
                # (Your existing code that sets st.session_state.target_time etc. is here)
                if "current_ch" not in st.session_state or st.session_state.current_ch != ch_choice:
                    st.session_state.current_ch = ch_choice
                    st.session_state.ch_start_time = time.time() 
                    
                    st.session_state.ch_type = random.choice(["time", "moves", "both"])
                    st.session_state.target_moves = random.randint(2, 5)
                    st.session_state.target_time = random.randint(10, 25)
                    
                    # 🌟 NEW: THE START ANIMATION (Toast)
                    st.toast("Ready? The clock is ticking! 🚀", icon="⏰")

                # 🌟 NEW: THE BOUNTY BOARD (Always visible)
                with st.container(border=True):
                    st.markdown("### 🏆 Bonus Goals")
                    
                    col_goal1, col_goal2 = st.columns(2)
                    
                    if st.session_state.ch_type in ["moves", "both"]:
                        col_goal1.info(f"🧩 **Moves:** Solve in **{st.session_state.target_moves}** gates or less (+5 Coins)")
                    else:
                        col_goal1.write("🧩 *No move limit this time!*")
                        
                    if st.session_state.ch_type in ["time", "both"]:
                        col_goal2.warning(f"⏱️ **Time:** Solve in **{st.session_state.target_time}** seconds or less (+5 Coins)")
                    else:
                        col_goal2.write("⏱️ *No time limit this time!*")
                    
                ch_data = challenges[ch_choice]
                num_q = ch_data["qubits"]
                target_sv = Statevector(ch_data["target"])
                ch_reward = ch_data["reward"]

                # 3. MISSION BRIEFING (Only shows if NOT cleared yet)
                if ch_choice not in st.session_state.cleared_levels:
                    with st.expander("📂 View Mission Briefing", expanded=True):
                        st.info(f"**Current Mission:** {ch_data['goal_text']} = {ch_data['output']}")
                        st.info(f"**Initial State:** {ch_data['initial_state']}")
                        st.write(f"Reference: {ch_data['reference']}")
                        st.write(f"**Reward for clearing:** {ch_reward} 🐈‍⬛")
                        if ch_choice in st.session_state.cleared_levels:
                            st.success("✅ Challenge completed!")

    # --- SESSION STATE & TIME MACHINE ---
                # --- SESSION STATE & TIME MACHINE ---
                if "active_ch" not in st.session_state or st.session_state.active_ch != ch_choice:
                    st.session_state.active_ch = ch_choice
                    st.session_state.qc = QuantumCircuit(num_q)
                    
                    # Custom starting states for specific challenges
                    if ch_choice == "Challenge C: Phase Kickback": 
                        st.session_state.qc.x(1) 
                    elif ch_choice == "Challenge E: The Un-Entangler":
                        st.session_state.qc.h(0)
                        st.session_state.qc.cx(0, 1)
                    elif ch_choice == "Challenge F: The Quantum Swap":
                        st.session_state.qc.x(1)

                    # Initialize the History
                    st.session_state.history = [st.session_state.qc.copy()]
                    st.session_state.history_idx = 0
                    st.session_state.checked = False
                    
                    # Initialize the History with the blank starting circuit
                    st.session_state.history = [st.session_state.qc.copy()]
                    st.session_state.history_idx = 0
                    st.session_state.checked = False

                qc = st.session_state.qc

                # --- HELPER FUNCTION: SAVE SNAPSHOT ---
                # This function runs every time a gate is clicked
                def save_state():
                    # If the user undid a few steps and then clicked a new gate, erase the "alternate future"
                    st.session_state.history = st.session_state.history[:st.session_state.history_idx + 1]
                    # Save a copy of the new circuit state
                    st.session_state.history.append(st.session_state.qc.copy())
                    # Move our timeline pointer forward
                    st.session_state.history_idx += 1        
            
            col_main, col_gates = st.columns([8,3])


                    # 2. SELECTION LOGIC

                        
            with col_gates:        # --- THE CIRCUIT VISUALIZER ---
                with st.container(border=True):

                    with st.expander("🛠️ Available Quantum Gates", expanded=True):
                
                # This loop automatically builds a row for however many qubits the challenge has!
                        for i in range(num_q):
                            st.markdown(f"**Qubit {i}**")
                    
                    # Create 4 tiny columns just for the buttons on this specific row
                            g1, g2, g3, g4 = st.columns(4)
                    
                            with g1:
                                if st.button("X", key=f"x{i}", use_container_width=True): qc.x(i);save_state()
                            with g2:
                                if st.button("Y", key=f"y{i}", use_container_width=True): qc.y(i);save_state()
                            with g3:
                                if st.button("Z", key=f"z{i}", use_container_width=True): qc.z(i);save_state()
                            with g4:
                                if st.button("H", key=f"h{i}", use_container_width=True): qc.h(i);save_state()
                        
                            st.divider() # Adds a neat line between qubits
                    
                # Multi-Qubit Gates (Placed at the very bottom, taking up the full width)
                        if num_q > 1:
                            st.markdown("**Two-Qubit Gates**")
                            if st.button("CNOT (Ctrl: q0, Targ: q1)", key="cx01", use_container_width=True): qc.cx(0, 1);save_state()
                            if st.button("CNOT (Ctrl: q1, Targ: q0)", key="cx10", use_container_width=True): qc.cx(1, 0);save_state() 
                        if num_q > 2:
                            st.markdown("**Three-Qubit Gates**")
                            if st.button("Toffoli (Ctrl: q0,q1, Targ: q2)", key="ccx012", use_container_width=True): qc.ccx(0, 1, 2);save_state()   
                            if st.button("Toffoli (Ctrl: q0,q2, Targ: q1)", key="ccx021", use_container_width=True): qc.ccx(0, 2, 1);save_state()
                            if st.button("Toffoli (Ctrl: q1,q2, Targ: q0)", key="ccx120", use_container_width=True): qc.ccx(1, 2, 0);save_state()
            with col_main:

                        
                    # 4. THE SCROLLABLE WORKSPACE
                        # This keeps the Header and Selector FIXED at the top while the workspace scrolls
                    with st.container(border=True):            # --- SESSION STATE & CIRCUIT ---
                        st.warning(f"{ch_data['initial_state']} to {ch_data['output']}")
                        # 3. SESSION STATE MANAGEMENT
                        # This resets the circuit ONLY when you switch to a DIFFERENT challenge
                            # For Challenge C, we start with q1 in the |1> state per the textbook

                        

                    # 4. UI DISPLAY    
                        # --- GATE BUTTONS ---
                        
                    with st.container(border=True):            # --- SESSION STATE & CIRCUIT ---
                        st.write("### Your Circuit Design:")
                        fig = qc.draw(output='mpl', initial_state=True)
                        st.pyplot(fig, use_container_width=False)

                    # --- THE CORNER CONTROLS ---
                    st.divider()
                    col_undo,col_check, col_reset,col_redo = st.columns([1,4,4,1])

                    with col_undo:
                    # Disable the button if we are at the start of the history
                        can_undo = st.session_state.history_idx > 0
                        if st.button("↩️", use_container_width=True, disabled=not can_undo):
                            st.session_state.history_idx -= 1
                            # Load the previous circuit copy
                            st.session_state.qc = st.session_state.history[st.session_state.history_idx].copy()
                            st.session_state.checked = False
                            st.rerun()
                    with col_check:
                        if st.button("Check Circuit", type="primary", use_container_width=True):
                            st.session_state.checked = True
                            
                    
                    with col_redo:
                    # Disable the button if we are at the end of the history
                        can_redo = st.session_state.history_idx < len(st.session_state.history) - 1
                        if st.button("↪️", use_container_width=True, disabled=not can_redo):
                            st.session_state.history_idx += 1
                            # Load the next circuit copy
                            st.session_state.qc = st.session_state.history[st.session_state.history_idx].copy()
                            st.session_state.checked = False
                            st.rerun()
                    with col_reset:
                        if st.button("Reset", use_container_width=True):
                            # Reset the circuit
                            st.session_state.qc = QuantumCircuit(num_q)
                            if ch_choice == "Challenge C: Phase Kickback": st.session_state.qc.x(1) 
                            
                            # Wipe the time machine clean!
                            st.session_state.history = [st.session_state.qc.copy()]
                            st.session_state.history_idx = 0
                            
                            st.session_state.checked = False
                            st.rerun()

                    # --- WIN LOGIC ---
                    if st.session_state.checked:
                        current_sv = Statevector(qc)
                        st.write("### 🔍 Results")
                        st.write("**Your Resulting State Vector:**")
                        st.code(np.round(current_sv.data, 3))
                        
                        # ... (Keep your math_string / LaTeX drawing here if you have it) ...

                        if Statevector(qc).equiv(target_sv):
                            # 1. FIX THE BUG: Check if it's a new clear BEFORE adding it
                            is_new_clear = ch_choice not in st.session_state.cleared_levels
                            
                            # 2. CALCULATE PERFORMANCE
                            moves_taken = len(qc.data) # Number of gates on the circuit
                            time_taken = int(time.time() - st.session_state.ch_start_time)
                            
                            # 3. DISPLAY STATS
                            st.write(f"⏱️ **Time:** {time_taken}s")
                            st.write(f"🔄 **Moves:** {moves_taken}")
                            
                            # 4. CALCULATE STARS AND BONUSES
                            stars = 1
                            bonus = 0
                            
                            # Evaluate based on the randomly assigned challenge type
                            if st.session_state.ch_type in ["moves", "both"]:
                                st.caption(f"🎯 Move Goal: {st.session_state.target_moves} or fewer")
                                if moves_taken <= st.session_state.target_moves:
                                    stars += 1
                                    bonus += 5
                                    
                            if st.session_state.ch_type in ["time", "both"]:
                                st.caption(f"🎯 Time Goal: {st.session_state.target_time}s or faster")
                                if time_taken <= st.session_state.target_time:
                                    stars += 1
                                    bonus += 5
                                    
                            # Draw the stars!
                    # Draw the stars!
                            star_display = "⭐" * stars + "🌑" * (3 - stars)
                            st.success(f"### {star_display} Challenge Cleared!")
                            
                            # 🌟 NEW: THE VICTORY ANIMATIONS!
                            if is_new_clear:
                                if stars == 3:
                                    st.balloons() # Triggers full-screen balloons for a perfect run!
                                # 5. PAYOUT THE COINS
                            if is_new_clear:
                                total_reward = ch_reward + bonus
                                # ... (rest of your existing coin logic) ...
                                
                                st.toast(f"🎉 Earned {total_reward} Catty-Coins ({ch_reward} base + {bonus} bonus)!", icon="🐈‍⬛")
                                
                                # (Optional: If you connected Supabase earlier, you should push the new coin total to the database here!)
                                
                            else:
                                st.info("You have already cleared this level, but great job improving your score!")
                                
                            st.session_state.checked = False # Reset the check button
                        else:
                            st.error("❌ Vector Mismatch. Try again.")
                            st.session_state.checked = False


    if current_page == "🧘‍♀️ Sandbox Mode":
        if "sb_qubits" not in st.session_state:
            st.session_state.sb_qubits = 3 # Default to 3 qubits
        if "sb_circuit_logic" not in st.session_state:
            st.session_state.sb_circuit_logic = []
        if "sb_redo_logic" not in st.session_state: # <--- NEW REDO MEMORY
            st.session_state.sb_redo_logic = [] # Stores our gates like [("H", 0), ("X", 1)]
        st.header("🧘‍♀️ Sandbox Mode: Free Play")
        def add_gate(gate, target, control1=None, control2=None):
            """Adds a gate to memory, with built-in quantum physics safety checks."""
            if control1 == target or control2 == target or (control1 == control2 and control1 is not None):
                st.toast("⚠️ Error: Control and Target qubits must all be different!", icon="🚨")
                return
        
            instruction = {"gate": gate, "target": target}
            if control1 is not None:
                instruction["control1"] = control1
            if control2 is not None:
                instruction["control2"] = control2
        
            st.session_state.sb_circuit_logic.append(instruction)

        def clear_sandbox():
            st.session_state.sb_circuit_logic = []

        def undo_gate():
            if len(st.session_state.sb_circuit_logic) > 0:
        # Pop the last gate off the circuit and save it to the redo list
                st.session_state.sb_redo_logic.append(st.session_state.sb_circuit_logic.pop())

        def redo_gate():
            if len(st.session_state.sb_redo_logic) > 0:
        # Pop the last gate off the redo list and put it back on the circuit
                st.session_state.sb_circuit_logic.append(st.session_state.sb_redo_logic.pop())

        def load_map(uploaded_json):
            """Reads a file and overwrites the sandbox memory."""
            if uploaded_json is not None:
                data = json.load(uploaded_json)
                st.session_state.sb_qubits = data["qubits"]
                st.session_state.sb_circuit_logic = data["logic"]
        def clear_sandbox():
            st.session_state.sb_circuit_logic = []
        # Top Control Panel
        col_controls, col_save = st.columns([2, 1])

        with col_controls:
            # Qubit Selector
            st.session_state.sb_qubits = st.slider("Select Number of Qubits", min_value=1, max_value=5, value=st.session_state.sb_qubits)
            b1, b2, b3 = st.columns(3)
    
    # We even use 'disabled' so they turn gray if there's nothing to undo/redo!
            b1.button("↩️ Undo", on_click=undo_gate, use_container_width=True, disabled=(len(st.session_state.sb_circuit_logic) == 0))
            b2.button("↪️ Redo", on_click=redo_gate, use_container_width=True, disabled=(len(st.session_state.sb_redo_logic) == 0))
            b3.button("🗑️ Clear", on_click=clear_sandbox, use_container_width=True)
                    # ==========================================
            # 5. THE ADVANCED GATE TOOLBOX
            # ==========================================
            st.write("### 🧰 Quantum Toolbox")

            # Create three selectors for our wiring
            col_tar, col_c1, col_c2 = st.columns(3)
            with col_tar:
                target_q = st.selectbox("🎯 Target Qubit:", range(st.session_state.sb_qubits), index=0)
            with col_c1:
                default_c1 = 1 if st.session_state.sb_qubits > 1 else 0
                ctrl_1 = st.selectbox("🔗 Control 1 (for CNOT/CCNOT):", range(st.session_state.sb_qubits), index=default_c1)
            with col_c2:
                default_c2 = 2 if st.session_state.sb_qubits > 2 else 0
                ctrl_2 = st.selectbox("🔗 Control 2 (for CCNOT):", range(st.session_state.sb_qubits), index=default_c2)

            st.divider()

            st.write("**Standard Gates (Applies to Target Qubit)**")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.button("Apply X", on_click=add_gate, args=("X", target_q))
            c2.button("Apply Y", on_click=add_gate, args=("Y", target_q))
            c3.button("Apply Z", on_click=add_gate, args=("Z", target_q))
            c4.button("Apply H", on_click=add_gate, args=("H", target_q))
            c5.button("Measure", on_click=add_gate, args=("M", target_q), type="primary")

            st.write("**Entanglement Gates**")
            c_m1, c_m2, _ = st.columns([1, 1, 2])
            c_m1.button("Apply CNOT (CX)", on_click=add_gate, args=("CX", target_q, ctrl_1))
            c_m2.button("Apply Toffoli (CCX)", on_click=add_gate, args=("CCX", target_q, ctrl_1, ctrl_2))
        with col_save:
            # --- 1. MAP SAVE SYSTEM ---
            map_data = json.dumps({
                "qubits": st.session_state.sb_qubits,
                "logic": st.session_state.sb_circuit_logic
            })
            st.download_button(
                label="💾 Export Map (Save)",
                data=map_data,
                file_name="my_quantum_map.json",
                mime="application/json",
                use_container_width=True
            )
            
            # --- 2. MAP LOAD SYSTEM ---
            uploaded_file = st.file_uploader("📂 Import Map (Load)", type="json")
            if uploaded_file is not None:
                st.button("Confirm Load", on_click=load_map, args=(uploaded_file,))
                
            st.divider() # A clean visual line
            
            # --- 3. DOWNLOAD RESULT SYSTEM ---
            # We do a lightning-fast background calculation to get the latest data
            temp_qc = QuantumCircuit(st.session_state.sb_qubits, st.session_state.sb_qubits)
            has_m = False
            
            # Rebuild the logic quickly
            for inst in st.session_state.sb_circuit_logic:
                g, t = inst["gate"], inst["target"]
                c1, c2 = inst.get("control1"), inst.get("control2")
                if g == "X": temp_qc.x(t)
                elif g == "Y": temp_qc.y(t)
                elif g == "Z": temp_qc.z(t)
                elif g == "H": temp_qc.h(t)
                elif g == "M": 
                    temp_qc.measure(t, t)
                    has_m = True
                elif g == "CX" and c1 is not None: temp_qc.cx(c1, t)
                elif g == "CCX" and c1 is not None and c2 is not None: temp_qc.ccx(c1, c2, t)
                
            try:
                # Package the math based on whether they measured it or not!
                if has_m:
                    sim = AerSimulator()
                    counts = sim.run(temp_qc, shots=1024).result().get_counts()
                    result_text = json.dumps({"circuit_state": "Collapsed (Measured)", "simulation_counts": counts}, indent=2)
                else:
                    sv = Statevector(temp_qc)
                    result_text = json.dumps({"circuit_state": "Superposition (Pure Math)", "probabilities": sv.probabilities_dict()}, indent=2)
                    
                st.download_button(
                    label="📊 Download Result Data",
                    data=result_text,
                    file_name="quantum_math_results.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception:
                # If the circuit is empty or broken, don't show the download button
                pass

        # ==========================================
        # 4. BUILD AND DRAW THE CIRCUIT
        # ==========================================
        # We rebuild the Qiskit circuit fresh every time based on the saved logic
        qc = QuantumCircuit(st.session_state.sb_qubits, st.session_state.sb_qubits)

     # Track if the user added any measurements
        has_measurements = False

        for instruction in st.session_state.sb_circuit_logic:
            g = instruction["gate"]
            t = instruction["target"]
            c1 = instruction.get("control1", None)
            c2 = instruction.get("control2", None)
            
            # Apply the gates to the Qiskit object
            if g == "X": qc.x(t)
            elif g == "Y": qc.y(t)
            elif g == "Z": qc.z(t)
            elif g == "H": qc.h(t)
            elif g == "M": 
                qc.measure(t, t) 
                has_measurements = True
            # The New Entanglement Gates!
            elif g == "CX" and c1 is not None: 
                qc.cx(c1, t)
            elif g == "CCX" and c1 is not None and c2 is not None:
                qc.ccx(c1, c2, t)

        # Draw it! (Assuming you are using matplotlib for visuals)
        with st.container(border=True):
            fig = qc.draw(output='mpl', scale=0.8)
            st.pyplot(fig, use_container_width=False)

            # --- DOWNLOAD CIRCUIT AS PNG ---
    # 1. Create a temporary memory buffer
            buf = io.BytesIO()
            
            # 2. Save the matplotlib figure into the buffer as a PNG
            fig.savefig(buf, format="png", bbox_inches="tight", transparent=False, facecolor="#F8F6F0")
            
            # 3. Create the download button
            st.download_button(
                label="🖼️ Download Circuit as PNG",
                data=buf.getvalue(),
                file_name="my_quantum_circuit.png",
                mime="image/png"
            )
            st.divider()


        # ==========================================
        # 6. QUANTUM VISUALIZERS
        # ==========================================
            # ==========================================
    # 6. QUANTUM VISUALIZERS (THE SMART BUTTON)
    # ==========================================
            if st.button("🔬 Calculate Output State", type="primary", use_container_width=True):
                
                # SCENARIO A: A collapsed circuit (Contains Measurements)
                if has_measurements:
                    st.write("### 🎲 Quantum Simulator Results")
                    st.warning("You added a Measurement gate! The wave function collapsed, so we can't show Dirac math anymore.")
                    st.write("We ran your circuit on a virtual quantum chip 1,024 times. Here are the results:")
                    
                    try:
                        sim = AerSimulator()
                        # Run the simulation
                        result = sim.run(qc, shots=1024).result()
                        counts = result.get_counts()
                        
                        fig_hist = plot_histogram(counts, figsize=(10, 3))
                        st.pyplot(fig_hist, use_container_width=False)
                    except Exception as e:
                        st.error(f"⚠️ Simulation Error: {e}")
                        
                # SCENARIO B: Pure Math (No Measurements)
                else:
                    try:
                        sv = Statevector(qc)
                        
                        st.write("### 🧮 Final Quantum State (Dirac Notation)")
                        math_string = sv.draw(output='latex_source')
                        st.latex(math_string)
                        
                        tab_probs, tab_bloch = st.tabs(["📊 Probabilities", "🌐 Bloch Spheres"])
                        
                        with tab_probs:
                            fig_hist = plot_histogram(sv.probabilities_dict(), figsize=(10, 3))
                            st.pyplot(fig_hist, use_container_width=False)
                            
                        with tab_bloch:
                            fig_bloch = plot_bloch_multivector(sv)
                            st.pyplot(fig_bloch, use_container_width=False)
                            
                    except Exception as e:
                        st.error(f"⚠️ Error details: {e}")


        
