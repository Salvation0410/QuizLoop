export type QuestionType = 'single' | 'multiple' | 'judge'
export type Difficulty = 'easy' | 'medium' | 'hard'

export interface Option { key: string; text: string }
export interface Question {
  id: string; type: QuestionType; stem: string; options: Option[]; answer: string[]
  explanation: string; knowledge_point: string; difficulty: Difficulty
}
export interface Quiz { quiz_id: string; title: string; summary: string; status: string; questions: Question[] }
export interface AnswerRecord { question_id: string; selected_answers: string[]; duration_ms: number }
export interface Attempt { attempt_id: string; correct_count: number; total_questions: number; accuracy: number; xp_earned: number; coins_earned: number }
export interface Report { report_id: string; quiz_id: string; accuracy: number; mastered_points: string[]; weak_points: string[]; three_line_summary: string[]; advice: string[]; share_quote: string }
export interface Stats { completed_questions: number; average_accuracy: number; total_xp: number; total_coins: number; streak_days: number; completed_quizzes: number }
export interface HistoryItem { quiz_id: string; title: string; summary: string; status: string; question_count: number; created_at: string }
