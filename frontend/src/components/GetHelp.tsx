import { Phone, X } from 'lucide-react'
import { useRef } from 'react'

export default function GetHelp() {
  const dialog = useRef<HTMLDialogElement>(null)
  return (
    <>
      <button
        className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-xl border border-sage/40 bg-white px-3 py-2 text-sm font-semibold text-pine transition hover:bg-mist"
        type="button"
        aria-haspopup="dialog"
        onClick={() => dialog.current?.showModal()}
      >
        <Phone aria-hidden="true" size={16} />
        Get help
      </button>
      <dialog
        ref={dialog}
        aria-labelledby="get-help-title"
        className="fixed inset-0 m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-lg overflow-y-auto rounded-3xl border border-line bg-white p-6 text-ink shadow-soft backdrop:bg-ink/50 sm:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-sage">
              Support in India
            </p>
            <h2 className="mt-2 font-display text-3xl font-semibold" id="get-help-title">
              You can reach out
            </h2>
          </div>
          <button
            autoFocus
            className="icon-button inline-flex"
            aria-label="Close help"
            type="button"
            onClick={() => dialog.current?.close()}
          >
            <X aria-hidden="true" size={18} />
          </button>
        </div>
        <p className="mt-4 text-sm leading-6 text-muted">
          You do not need a low mood score to ask for support. These services connect you with
          people who can help.
        </p>
        <section
          className="mt-6 rounded-2xl border border-line bg-canvas p-5"
          aria-labelledby="tele-manas-title"
        >
          <h3 className="text-lg font-semibold" id="tele-manas-title">
            Tele-MANAS
          </h3>
          <p className="mt-2 text-sm leading-6 text-muted">
            Free, confidential mental health support, available 24/7 across India. Speak with a
            trained counsellor in English or a regional language.
          </p>
          <a
            className="button-primary mt-4"
            href="tel:+9114416?oai_link_source=model_response_hotline"
          >
            <Phone aria-hidden="true" size={16} />
            14416
          </a>
          <a
            className="text-link mt-3 block text-sm"
            href="https://telemanas.mohfw.gov.in/home?oai_link_source=model_response_hotline"
            target="_blank"
            rel="noreferrer"
          >
            Official Tele-MANAS website
          </a>
        </section>
        <section
          className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-5"
          aria-labelledby="emergency-help-title"
        >
          <h3 className="text-lg font-semibold" id="emergency-help-title">
            Immediate emergency
          </h3>
          <p className="mt-2 text-sm leading-6">
            If you or someone nearby is in immediate danger, call India's emergency response service
            for police, fire or medical assistance.
          </p>
          <a className="button-primary mt-4" href="tel:112">
            <Phone aria-hidden="true" size={16} />
            112
          </a>
          <a
            className="text-link mt-3 block text-sm"
            href="https://112.gov.in/"
            target="_blank"
            rel="noreferrer"
          >
            Official emergency service website
          </a>
        </section>
        <p className="mt-5 text-xs leading-5 text-muted">
          Numbers verified on 13 October 2026. MindMate does not place a call automatically; choose
          a number to open your device's calling app.
        </p>
      </dialog>
    </>
  )
}
