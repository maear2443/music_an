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
        self.analysis_data = None # 전체 분석 데이터를 저장할 변수
        self.root.title("Music to Suno Prompt Analyzer v2.0")
        self.root.geometry("800x800")
        self.root.minsize(700, 600)

        # --- 상단 프레임: 파일 선택 및 분석 ---
        top_frame = tk.Frame(self.root, pady=5)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.select_button = tk.Button(top_frame, text="1. 음악 파일 선택", command=self.select_file)
        self.select_button.pack(side=tk.LEFT)

        self.analyze_button = tk.Button(top_frame, text="2. 분석 시작", command=self.start_analysis_thread, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=10)

        self.file_label = tk.Label(top_frame, text="파일이 선택되지 않았습니다.", wraplength=400, justify=tk.LEFT)
        self.file_label.pack(side=tk.LEFT, padx=10)

        # --- 상태 로그 프레임 ---
        status_frame = tk.Frame(self.root, padx=10)
        status_frame.pack(fill=tk.X, pady=(5,0))
        tk.Label(status_frame, text="상태 로그:").pack(anchor=tk.W)
        self.status_text = self._create_text_widget(status_frame, height=5)

        # --- 메인 콘텐츠 (결과 + 가사)를 담을 PanedWindow ---
        main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 분석 결과 프레임 ---
        result_frame = tk.Frame(main_pane, pady=5)
        tk.Label(result_frame, text="분석 결과 및 Suno 프롬프트:").pack(anchor=tk.W)
        self.result_text = self._create_text_widget(result_frame, height=10)
        main_pane.add(result_frame, stretch="always")

        # --- 가사 프레임 ---
        lyrics_frame = tk.Frame(main_pane, pady=5)
        tk.Label(lyrics_frame, text="추출된 가사 (타임스탬프):").pack(anchor=tk.W)
        self.lyrics_text = self._create_text_widget(lyrics_frame, height=12)
        main_pane.add(lyrics_frame, stretch="always")

        # --- 하단 버튼 프레임 ---
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.copy_button = tk.Button(bottom_frame, text="프롬프트 복사", state=tk.DISABLED, command=self.copy_prompt_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.export_srt_button = tk.Button(bottom_frame, text="SRT로 내보내기", state=tk.DISABLED, command=self.export_to_srt)
        self.export_srt_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

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

    def export_to_srt(self):
        """재구성된 줄 단위 가사 데이터를 표준 .srt 파일로 저장합니다."""
        if not self.analysis_data or "reconstructed_lyrics" not in self.analysis_data or not self.analysis_data["reconstructed_lyrics"]:
            self.log_status("오류: 내보낼 가사 데이터가 없거나, 아직 줄 단위로 재구성되지 않았습니다.")
            return

        try:
            srt_content = []
            # 재구성된 줄 단위 가사를 사용합니다.
            lyrics = self.analysis_data["reconstructed_lyrics"]
            for i, item in enumerate(lyrics):
                sequence = i + 1
                start_time = item.get("start", "00:00:00,000")
                end_time = item.get("end", "00:00:00,000")
                lyric_text = item.get("lyric", "")

                srt_block = f"{sequence}\n{start_time} --> {end_time}\n{lyric_text}\n"
                srt_content.append(srt_block)

            full_srt_text = "\n".join(srt_content)

            # 사용자에게 파일 저장 경로를 묻습니다.
            filepath = filedialog.asksaveasfilename(
                title="SRT 파일로 저장",
                defaultextension=".srt",
                filetypes=(("SubRip Subtitle", "*.srt"), ("All files", "*.*"))
            )

            if filepath:
                # UTF-8-SIG 인코딩은 Windows 메모장에서의 호환성을 높여줍니다.
                with open(filepath, 'w', encoding='utf-8-sig') as f:
                    f.write(full_srt_text)
                self.log_status(f"가사가 {os.path.basename(filepath)} 파일로 성공적으로 저장되었습니다.")
            else:
                self.log_status("SRT 파일 저장이 취소되었습니다.")

        except Exception as e:
            self.log_status(f"SRT 파일 저장 중 오류 발생: {e}")

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

    def _time_str_to_ms(self, time_str):
        """HH:MM:SS,ms 형식의 시간 문자열을 밀리초(ms)로 변환합니다."""
        parts = time_str.split(',')
        h, m, s = map(int, parts[0].split(':'))
        ms = int(parts[1])
        return (h * 3600 + m * 60 + s) * 1000 + ms

    def _reconstruct_lines_from_words(self, word_level_lyrics, pause_threshold_ms=700):
        """단어 단위 가사 데이터를 줄 단위로 재구성합니다."""
        if not word_level_lyrics:
            return []

        lines = []
        current_line_words = [word_level_lyrics[0]]

        for i in range(1, len(word_level_lyrics)):
            prev_word = word_level_lyrics[i-1]
            current_word = word_level_lyrics[i]

            try:
                prev_end_ms = self._time_str_to_ms(prev_word['end'])
                current_start_ms = self._time_str_to_ms(current_word['start'])
                pause_duration = current_start_ms - prev_end_ms

                if pause_duration > pause_threshold_ms:
                    # 줄바꿈으로 간주
                    line_text = " ".join(w['word'] for w in current_line_words)
                    line_start = current_line_words[0]['start']
                    line_end = current_line_words[-1]['end']
                    lines.append({"start": line_start, "end": line_end, "lyric": line_text})
                    current_line_words = [current_word]
                else:
                    current_line_words.append(current_word)
            except (ValueError, KeyError):
                # 타임스탬프 형식이 잘못된 경우, 현재 단어를 새 줄로 처리
                if current_line_words:
                    line_text = " ".join(w['word'] for w in current_line_words)
                    line_start = current_line_words[0].get('start', 'N/A')
                    line_end = current_line_words[-1].get('end', 'N/A')
                    lines.append({"start": line_start, "end": line_end, "lyric": line_text})
                current_line_words = [current_word]


        # 마지막 줄 추가
        if current_line_words:
            line_text = " ".join(w['word'] for w in current_line_words)
            line_start = current_line_words[0]['start']
            line_end = current_line_words[-1]['end']
            lines.append({"start": line_start, "end": line_end, "lyric": line_text})

        return lines

    def process_and_display_results(self, result_text):
        """Gemini 응답을 파싱하고, 결과를 각 영역에 맞게 생성 및 표시합니다."""
        try:
            self.log_status("분석 결과 파싱 중...")
            self.analysis_data = None
            self.root.after(0, self._update_text_widget, self.result_text, "", True)
            self.root.after(0, self._update_text_widget, self.lyrics_text, "", True)

            cleaned_text = result_text.strip().replace("```json", "").replace("```", "")
            self.analysis_data = json.loads(cleaned_text)

            # 1. 분석 요약 및 Suno 프롬프트 표시
            suno_prompt = self.generate_suno_prompt(self.analysis_data)
            analysis_summary = self.format_analysis_summary(self.analysis_data)
            result_display_text = f"--- 분석 요약 ---\n{analysis_summary}\n\n--- 생성된 Suno AI 프롬프트 ---\n{suno_prompt}"
            self.root.after(0, self._update_text_widget, self.result_text, result_display_text, True)
            self.root.after(0, lambda: self.copy_button.config(state=tk.NORMAL))

            # 2. 단어 단위 가사를 줄 단위로 재구성하여 표시
            word_lyrics = self.analysis_data.get("lyrics", [])
            if word_lyrics:
                self.log_status("단어 단위 가사를 줄 단위로 재구성 중...")
                reconstructed_lines = self._reconstruct_lines_from_words(word_lyrics)
                self.analysis_data['reconstructed_lyrics'] = reconstructed_lines # SRT 내보내기를 위해 저장

                lyrics_display_text = "\n".join([f"[{line.get('start')} --> {line.get('end')}] {line.get('lyric')}" for line in reconstructed_lines])
                self.root.after(0, self._update_text_widget, self.lyrics_text, lyrics_display_text, True)
                self.root.after(0, lambda: self.export_srt_button.config(state=tk.NORMAL))
                self.log_status("가사 재구성 및 표시 완료!")
            else:
                self.root.after(0, self._update_text_widget, self.lyrics_text, "추출된 가사가 없습니다.", True)
                self.root.after(0, lambda: self.export_srt_button.config(state=tk.DISABLED))

        except json.JSONDecodeError:
            error_msg = "오류: Gemini로부터 받은 분석 결과를 파싱하는데 실패했습니다. 원본 출력을 표시합니다."
            self.log_status(error_msg)
            self.root.after(0, self._update_text_widget, self.result_text, result_text, True)
        except Exception as e:
            error_msg = f"결과 처리 중 오류 발생: {e}"
            self.log_status(error_msg)
            self.root.after(0, self._update_text_widget, self.result_text, result_text, True)

    def format_analysis_summary(self, data):
        """분석 데이터를 요약 텍스트로 포맷팅합니다."""
        try:
            genre = data.get("genre", "정보 없음")
            chords = data.get("chords", "정보 없음")
            bpm = data.get("bpm", 0)
            emotions = data.get("emotions", [])
            emotion_lines = [f"- {e.get('emotion', '알 수 없음')}: {e.get('percentage', 0)}%" for e in emotions]
            emotion_summary = "\n".join(emotion_lines)
            return f"장르: {genre}\n코드: {chords}\nBPM: {bpm}\n감정 분석:\n{emotion_summary}"
        except Exception:
            return "분석 데이터 요약에 실패했습니다."

    def generate_suno_prompt(self, data):
        """분석 데이터를 기반으로 Suno AI 프롬프트 문자열을 생성합니다."""
        try:
            genre = data.get("genre", "unknown genre")
            chords = data.get("chords", "a simple")
            bpm = data.get("bpm", 120)
            emotions = data.get("emotions", [])
            emotions.sort(key=lambda x: x.get('percentage', 0), reverse=True)
            emotion_names = [e.get('emotion', '') for e in emotions]
            emotion_str = ", ".join(emotion_names[:3]) if emotion_names else "unique"
            return f"A song in the style of {genre}, featuring a {chords} chord progression. The overall mood is {emotion_str}. The tempo is around {bpm} BPM."
        except Exception as e:
            self.log_status(f"프롬프트 생성 중 오류: {e}")
            return "Could not generate prompt from the provided data."

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
            You are a world-class music analyst. Your task is to analyze the provided audio file and return ONLY a single, valid JSON object in KOREAN.
            Do not include any explanatory text or markdown formatting.

            **CRITICAL INSTRUCTIONS FOR ACCURATE, WORD-LEVEL LYRICS:**
            1.  You MUST transcribe the ENTIRE song from beginning to end. Do NOT summarize or omit any lyrics.
            2.  The "lyrics" key in the JSON must be an array of WORD objects. DO NOT provide line-level timestamps.
            3.  Each object in the "lyrics" array must represent a single word and have three keys: "word" (the transcribed word in Korean), "start" (the word's start time in "HH:MM:SS,ms" format), and "end" (the word's end time in "HH:MM:SS,ms" format).
            4.  If the song is instrumental, return an empty array [] for the "lyrics" key.

            The JSON object must contain the following keys:
            - "genre": A string describing the primary genre in Korean.
            - "chords": A string representing the main chord progression.
            - "bpm": An integer for the beats per minute.
            - "emotions": An array of 6 objects, each with "emotion" (in Korean) and "percentage" keys.
            - "lyrics": An array of WORD-LEVEL timestamp objects as described above.

            Example of the "lyrics" array structure:
            "lyrics": [
              {"word": "첫", "start": "00:00:15,250", "end": "00:00:15,450"},
              {"word": "번째", "start": "00:00:15,450", "end": "00:00:15,800"},
              {"word": "가사", "start": "00:00:15,900", "end": "00:00:16,300"}
            ]
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
