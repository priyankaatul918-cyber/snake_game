import random
import time
from typing import List, Tuple

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw


GridPos = Tuple[int, int]


def init_game(grid_size=20):
    mid = grid_size // 2
    snake = [(mid, mid), (mid - 1, mid), (mid - 2, mid)]
    direction = "RIGHT"
    apple = place_apple(grid_size, snake)
    st.session_state.update({
        "grid_size": grid_size,
        "snake": snake,
        "direction": direction,
        "apple": apple,
        "score": 0,
        "game_over": False,
        "speed": 6.0,
    })


def place_apple(grid_size: int, snake: List[GridPos]) -> GridPos:
    while True:
        pos = (random.randrange(grid_size), random.randrange(grid_size))
        if pos not in snake:
            return pos


def turn_direction(new_dir: str):
    # prevent reversing
    opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
    cur = st.session_state.direction
    if new_dir == cur or new_dir == opposites.get(cur):
        return
    st.session_state.direction = new_dir


def move_snake():
    if st.session_state.game_over:
        return

    snake = st.session_state.snake.copy()
    head_x, head_y = snake[0]
    d = st.session_state.direction
    if d == "UP":
        new_head = (head_x, head_y - 1)
    elif d == "DOWN":
        new_head = (head_x, head_y + 1)
    elif d == "LEFT":
        new_head = (head_x - 1, head_y)
    else:
        new_head = (head_x + 1, head_y)

    grid = st.session_state.grid_size
    # check wall collision
    x, y = new_head
    if x < 0 or y < 0 or x >= grid or y >= grid or new_head in snake:
        st.session_state.game_over = True
        return

    snake.insert(0, new_head)
    if new_head == st.session_state.apple:
        st.session_state.score += 1
        st.session_state.apple = place_apple(grid, snake)
    else:
        snake.pop()

    st.session_state.snake = snake


def draw_board(cell_px=20) -> Image.Image:
    grid = st.session_state.grid_size
    size = grid * cell_px
    img = Image.new("RGB", (size, size), "#0b1020")
    draw = ImageDraw.Draw(img)

    # draw grid subtle lines
    for i in range(grid + 1):
        x = i * cell_px
        draw.line([(x, 0), (x, size)], fill="#0f1724")
        draw.line([(0, x), (size, x)], fill="#0f1724")

    # draw apple
    ax, ay = st.session_state.apple
    draw.rectangle(
        [ax * cell_px + 2, ay * cell_px + 2, (ax + 1) * cell_px - 2, (ay + 1) * cell_px - 2],
        fill="#ff4d4d",
    )

    # draw snake
    for i, (sx, sy) in enumerate(st.session_state.snake):
        color = "#47c754" if i > 0 else "#18a558"
        draw.rectangle(
            [sx * cell_px + 2, sy * cell_px + 2, (sx + 1) * cell_px - 2, (sy + 1) * cell_px - 2],
            fill=color,
        )

    return img


def trigger_rerun():
    """Try to trigger a Streamlit rerun in a few ways for compatibility across versions."""
    # Preferred API when available
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass

    # Fallback: change query params which causes a rerun (new API: assign to st.query_params)
    try:
        st.query_params = {"_rerun": int(time.time() * 1000)}
        return
    except Exception:
        pass

    # Final fallback: raise internal RerunException if present
    try:
        from streamlit.runtime.scriptrunner import RerunException

        raise RerunException
    except Exception:
        # Can't force a rerun — give up silently
        return

def main():
    st.set_page_config(page_title="Snake — Streamlit", page_icon="🟩", layout="wide")
    st.title("Snake — Streamlit")

    if "snake" not in st.session_state:
        init_game(grid_size=20)

    # On-screen hint for controls
    st.info("Click the page to focus then use Arrow keys or WASD to control the snake. Hold a key for continuous movement when Autoplay is off.")

    # more square layout with smaller game area 
    col1, col2 = st.columns([1.5, 1])

    with col1:
        # reduced cell size by 20% (from 14px to 11px)
        img = draw_board(cell_px=11)
        # use width='stretch' per modern Streamlit API
        st.image(img, width='stretch')

    with col2:
        st.markdown(f"**Score:** {st.session_state.score}")
        st.markdown(f"**Snake length:** {len(st.session_state.snake)}")
        if st.session_state.game_over:
            st.error("Game Over — press Restart to play again")
            
        st.write("---")
        st.subheader("Controls")
        up, _, _ = st.columns([1, 0.2, 1])
        with up:
            if st.button("⬆ Up"):
                turn_direction("UP")

        left, middle, right = st.columns([1, 0.8, 1])
        with left:
            if st.button("⬅ Left"):
                turn_direction("LEFT")
        with middle:
            if st.button("Restart"):
                init_game(st.session_state.grid_size)
        with right:
            if st.button("Right ➡"):
                turn_direction("RIGHT")

        down1, _, down2 = st.columns([1, 0.2, 1])
        with down1:
            pass
        with down2:
            if st.button("⬇ Down"):
                turn_direction("DOWN")

        st.write("---")
        speed = st.slider("Speed (moves/sec)", min_value=1.0, max_value=15.0, value=float(st.session_state.speed))
        st.session_state.speed = speed

        autoplay = st.checkbox("Autoplay", value=False)
        step = st.button("Step")

    # Add keyboard listener component after controls
    key = components.html(
        """
        <script>
        const send = (k) => { Streamlit.setComponentValue(k); };
        const pressed = new Set();
        let lastKey = null;

        const mapKey = (k) => {
            if (!k) return null;
            if (k.startsWith('Arrow')) return k;
            return k.length===1 ? k.toLowerCase() : k;
        }

        document.addEventListener('keydown', (e) => {
            const k = mapKey(e.key);
            const supported = ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','w','a','s','d'];
            if (supported.includes(k)) {
                e.preventDefault();
                pressed.add(k);
                lastKey = k;
                send(k);  // send immediately on keydown
            }
        });

        document.addEventListener('keyup', (e) => {
            const k = mapKey(e.key);
            if (pressed.has(k)) {
                pressed.delete(k);
                if (lastKey === k) {
                    lastKey = pressed.size ? Array.from(pressed).pop() : null;
                }
            }
        });

        window.addEventListener('blur', () => { pressed.clear(); lastKey = null; });

        // send current key at interval for continuous movement
        setInterval(() => { if (lastKey) send(lastKey); }, 80);

        Streamlit.setComponentValue('');
        </script>
        """,
        height=1,
    )

    if key:
        mapping = {
            'ArrowUp': 'UP', 
            'ArrowDown': 'DOWN',
            'ArrowLeft': 'LEFT',
            'ArrowRight': 'RIGHT',
            'w': 'UP',
            's': 'DOWN',
            'a': 'LEFT',
            'd': 'RIGHT',
        }
        dir_to_set = mapping.get(key)
        if dir_to_set:
            turn_direction(dir_to_set)
            # Move immediately when not in autoplay
            if not autoplay and not st.session_state.game_over:
                move_snake()
                trigger_rerun()  # ensure we see the movement right away

    # step when pressing Step or autoplay
    if not st.session_state.game_over and (step or autoplay):
        move_snake()

        # when autoplay is on, wait then rerun to animate
        if autoplay and not st.session_state.game_over:
            # small sleep proportional to speed
            time.sleep(max(0.05, 1.0 / st.session_state.speed))
            trigger_rerun()


if __name__ == "__main__":
    main()
