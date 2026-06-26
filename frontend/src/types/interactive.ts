/** Animation types supported by the advanced interactive material system. */
export type AnimationType =
  | 'sort_animation'
  | 'data_structure'
  | 'flowchart_step'
  | 'formula_derivation'
  | 'code_execution'

/** A single animation item (one per knowledge point). */
export interface AnimationItem {
  knowledge_point: string
  animation_type: AnimationType
  title: string
  description: string
  explanation: string
  /** Path to the rendered HTML file (relative URL, e.g. /assets/...) */
  html_path?: string
  // Sort animation fields
  algorithm_name?: string
  initial_array?: number[]
  element_count?: number
  // Data structure fields
  ds_type?: string
  ds_type_name?: string
  // Code execution fields
  code_filename?: string
  code_lines?: string[]
  // Formula derivation fields
  initial_formula?: string
}

/** Interactive exercise types. */
export type ExerciseType = 'drag_sort' | 'fill_blank' | 'choice'

export interface DragSortExercise {
  type: 'drag_sort'
  instruction: string
  items: string[]
  correct_order: number[]
}

export interface FillBlankExercise {
  type: 'fill_blank'
  instruction: string
  blanks: { prompt?: string; placeholder?: string; answer: string }[]
}

export interface ChoiceExercise {
  type: 'choice'
  instruction: string
  question: string
  options: (string | { value: string; label: string })[]
  answer: string
  explanation?: string
}

export type InteractiveExercise = DragSortExercise | FillBlankExercise | ChoiceExercise

export interface GlossaryTerm {
  term: string
  definition: string
}

/** Top-level interactive content structure (matches backend JSON output). */
export interface InteractiveContent {
  title: string
  animations: AnimationItem[]
  html_files: string[]
  exercises: InteractiveExercise[]
  glossary: GlossaryTerm[]
}
