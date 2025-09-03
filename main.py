import tkinter as tk
from tkinter import filedialog
import os
import threading
import json
import google.generativeai as genai

class MusicAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.filepath = None
        self.root.title("Music to Suno Prompt Analyzer")
        self.root.geometry("700x650")
        self.root.minsize(600, 500)

        # --- 상단 프레임: 파일 선택 및 분석 버튼 ---
        top_frame = tk.Frame(self.root, pady=5)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.select_button = tk.Button(top_frame, text="1. 음악 파일 선택", command=self.select_file)
        self.select_button.pack(side=tk.LEFT)

        self.analyze_button = tk.Button(top_frame, text="2. 분석 시작", command=self.start_analysis_thread, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=10)

        self.file_label = tk.Label(top_frame, text="파일이 선택되지 않았습니다.", wraplength=400, justify=tk.LEFT)
        self.file_label.pack(side=tk.LEFT, padx=10)

        # --- 중간 프레임: 상태 로그 ---
        status_frame = tk.Frame(self.root, padx=10)
        status_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(status_frame, text="상태 로그:").pack(anchor=tk.W)
        self.status_text = self._create_text_widget(status_frame, height=8)

        # --- 하단 프레임: 분석 결과 ---
        result_frame = tk.Frame(self.root, padx=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(result_frame, text="분석 결과 및 Suno 프롬프트:").pack(anchor=tk.W)
        self.result_text = self._create_text_widget(result_frame, height=10)

        # --- 최하단: 복사 버튼 ---
        self.copy_button = tk.Button(self.root, text="프롬프트 복사", state=tk.DISABLED, command=self.copy_prompt_to_clipboard)
        self.copy_button.pack(pady=10)

    def copy_prompt_to_clipboard(self):
        """결과 텍스트 영역에서 Suno 프롬프트만 추출하여 클립보드에 복사합니다."""
        try:
            full_text = self.result_text.get("1.0", tk.END)
            header = "--- 생성된 Suno AI 프롬프트 ---\n"

            prompt_start_index = full_text.find(header)
            if prompt_start_index != -1:
                prompt_text = full_text[prompt_start_index + len(header):].strip()
                if prompt_text:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(prompt_text)
                    self.log_status("프롬프트가 클립보드에 복사되었습니다!")

                    original_text = self.copy_button.cget("text")
                    self.copy_button.config(text="복사 완료!", state=tk.DISABLED)
                    self.root.after(2000, lambda: self.copy_button.config(text=original_text, state=tk.NORMAL if self.result_text.get("1.0", tk.END).strip() else tk.DISABLED))
                else:
                    self.log_status("오류: 복사할 프롬프트가 없습니다.")
            else:
                self.log_status("오류: 복사할 프롬프트를 찾을 수 없습니다.")
        except Exception as e:
            self.log_status(f"클립보드 복사 중 오류 발생: {e}")

    def _create_text_widget(self, parent, **kwargs):
        text_widget = tk.Text(parent, state=tk.DISABLED, bg="#f0f0f0", **kwargs)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(2, 10))
        return text_widget

    def _update_text_widget(self, widget, message, clear=False):
        widget.config(state=tk.NORMAL)
        if clear:
            widget.delete('1.0', tk.END)
        widget.insert(tk.END, message + "\n")
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def log_status(self, message):
        self.root.after(0, self._update_text_widget, self.status_text, message)

    def process_and_display_results(self, result_text):
        """Gemini 응답을 파싱하고, Suno 프롬프트를 생성하며, 결과를 표시합니다."""
        try:
            self.log_status("분석 결과 파싱 중...")
            # Gemini 응답에서 Markdown 코드 블록 정리
            cleaned_text = result_text.strip().replace("```json", "").replace("```", "")
            analysis_data = json.loads(cleaned_text)

            suno_prompt = self.generate_suno_prompt(analysis_data)

            # 표시용으로 JSON을 예쁘게 포맷팅
            pretty_json = json.dumps(analysis_data, indent=2, ensure_ascii=False)

            display_text = (
                "--- Gemini 분석 데이터 ---\n"
                f"{pretty_json}\n\n"
                "--- 생성된 Suno AI 프롬프트 ---\n"
                f"{suno_prompt}"
            )

            self.root.after(0, self._update_text_widget, self.result_text, display_text, True)
            self.log_status("Suno AI 프롬프트가 성공적으로 생성되었습니다!")
            # 프롬프트가 생성되었으므로 복사 버튼 활성화
            self.root.after(0, lambda: self.copy_button.config(state=tk.NORMAL))

        except json.JSONDecodeError:
            error_msg = "오류: Gemini로부터 받은 분석 결과를 파싱하는데 실패했습니다. 원본 출력을 표시합니다."
            self.log_status(error_msg)
            self.root.after(0, self._update_text_widget, self.result_text, result_text, True)
        except Exception as e:
            error_msg = f"결과 처리 중 오류 발생: {e}"
            self.log_status(error_msg)
            self.root.after(0, self._update_text_widget, self.result_text, result_text, True)

    def generate_suno_prompt(self, data):
        """분석 데이터를 기반으로 Suno AI 프롬프트 문자열을 생성합니다."""
        try:
            genre = data.get("genre", "알 수 없는 장르")
            chords = data.get("chords", "단순한")
            bpm = data.get("bpm", 120)
            emotions = data.get("emotions", [])

            emotion_str = ", ".join(emotions) if emotions else "독특한"

            prompt = (
                f"A song in the style of {genre}, featuring a {chords} chord progression. "
                f"The overall mood is {emotion_str}. "
                f"The tempo is around {bpm} BPM."
            )
            return prompt
        except Exception as e:
            self.log_status(f"프롬프트 생성 중 오류: {e}")
            return "제공된 데이터로 프롬프트를 생성할 수 없습니다."

    def select_file(self):
        self.filepath = filedialog.askopenfilename(
            title="음악 파일을 선택하세요",
            filetypes=(("음악 파일", "*.mp3 *.wav"), ("모든 파일", "*.*"))
        )
        if self.filepath:
            filename = os.path.basename(self.filepath)
            self.file_label.config(text=f"선택됨: {filename}")
            self.analyze_button.config(state=tk.NORMAL)
            self.log_status(f"파일 선택됨: {filename}\n'분석 시작' 버튼을 눌러주세요.")
        else:
            self.file_label.config(text="파일이 선택되지 않았습니다.")
            self.analyze_button.config(state=tk.DISABLED)

    def start_analysis_thread(self):
        if not self.filepath:
            self.log_status("오류: 먼저 파일을 선택해주세요.")
            return

        self.select_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)

        for widget in [self.status_text, self.result_text]:
            widget.config(state=tk.NORMAL)
            widget.delete('1.0', tk.END)
            widget.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.analyze_music)
        thread.daemon = True
        thread.start()

    def analyze_music(self):
        try:
            self.log_status("API 키를 확인하는 중...")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                self.log_status("오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
                self.log_status("프로그램을 종료하고 API 키를 설정해주세요.")
                return

            genai.configure(api_key=api_key)
            self.log_status(f"파일 업로드 중: {os.path.basename(self.filepath)}...")

            music_file = genai.upload_file(path=self.filepath)
            self.log_status("파일 업로드 완료. Gemini가 분석을 시작합니다... (파일 크기에 따라 수 분 소요될 수 있습니다)")

            model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

            prompt = """
            You are a world-class music analyst. Your task is to analyze the provided audio file and return ONLY a single, valid JSON object.
            Do not include any explanatory text, markdown formatting like ```json, or anything else outside of the JSON object itself.

            The JSON object must contain the following keys:
            - "genre": A string describing the primary genre (e.g., "Indie Pop", "Orchestral Soundtrack", "Classic Rock").
            - "chords": A string representing the main chord progression (e.g., "C-G-Am-F"). If complex, provide the most prominent one.
            - "bpm": An integer for the beats per minute.
            - "emotions": An array of exactly 6 strings describing the dominant moods (e.g., "uplifting", "melancholy", "energetic", "peaceful", "dramatic", "joyful").
            """

            response = model.generate_content([prompt, music_file], request_options={'timeout': 600})

            self.log_status("음악 분석 완료!")
            self.process_and_display_results(response.text)

        except Exception as e:
            self.log_status(f"치명적인 오류 발생: {e}")
        finally:
            self.root.after(0, lambda: self.select_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.analyze_button.config(state=tk.NORMAL if self.filepath else tk.DISABLED))

if __name__ == "__main__":
    # 사용법 안내
    print("--------------------------------------------------")
    print("Music to Suno Prompt Analyzer")
    print("--------------------------------------------------")
    print("이 프로그램을 실행하기 전에, Google AI Studio에서 발급받은")
    print("API 키를 환경 변수로 설정해야 합니다.")
    print("\nWindows (cmd):")
    print('set GEMINI_API_KEY="YOUR_API_KEY"')
    print("\nWindows (PowerShell):")
    print('$env:GEMINI_API_KEY="YOUR_API_KEY"')
    print("\nmacOS / Linux:")
    print('export GEMINI_API_KEY="YOUR_API_KEY"')
    print("--------------------------------------------------")

    root = tk.Tk()
    app = MusicAnalyzerApp(root)
    root.mainloop()
