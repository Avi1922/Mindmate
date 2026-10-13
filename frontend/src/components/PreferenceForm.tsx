import { preferenceOptions, type Preferences } from '../lib/wellness'
const labels = {
  goal: 'What would you like MindMate to help with?',
  support_style: 'What kind of support feels helpful?',
  calming_activity: 'What helps you unwind?',
  check_in_time: 'When does a check-in fit your day?',
}
export default function PreferenceForm({
  value,
  onChange,
}: {
  value: Preferences
  onChange: (value: Preferences) => void
}) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      {Object.entries(preferenceOptions).map(([key, options]) => (
        <label className="field-label" key={key}>
          {labels[key as keyof typeof labels]}
          <select
            className="field-input"
            value={value[key as keyof typeof preferenceOptions]}
            onChange={(e) => onChange({ ...value, [key]: e.target.value })}
          >
            <option value="">Prefer not to answer</option>
            {options.map((option) => (
              <option key={option}>{option}</option>
            ))}
          </select>
        </label>
      ))}
    </div>
  )
}
