import { INSTAGRAM_URL, TIKTOK_URL, WHATSAPP_URL } from "./constants";
import { InstagramIcon, TikTokIcon, WhatsAppIcon } from "./icons";

const FLOAT_BTN =
  "flex h-14 w-14 items-center justify-center rounded-full text-white shadow-lg transition hover:scale-105 hover:shadow-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2";

export function FloatingSocialLinks() {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 items-center" aria-label="Redes sociales">
      <a
        href={INSTAGRAM_URL}
        target="_blank"
        rel="noopener noreferrer"
        className={`${FLOAT_BTN} bg-gradient-to-br from-[#833AB4] via-[#FD1D1D] to-[#FCAF45] focus-visible:outline-[#833AB4]`}
        aria-label="Síguenos en Instagram"
      >
        <InstagramIcon className="w-7 h-7" />
      </a>
      <a
        href={TIKTOK_URL}
        target="_blank"
        rel="noopener noreferrer"
        className={`${FLOAT_BTN} bg-black focus-visible:outline-black`}
        aria-label="Síguenos en TikTok"
      >
        <TikTokIcon className="w-7 h-7" />
      </a>
      <a
        href={WHATSAPP_URL}
        target="_blank"
        rel="noopener noreferrer"
        className={`${FLOAT_BTN} landing-whatsapp-float bg-[#25D366] focus-visible:outline-[#25D366]`}
        aria-label="Escríbenos por WhatsApp"
      >
        <WhatsAppIcon className="w-7 h-7" />
      </a>
    </div>
  );
}

/** @deprecated Use FloatingSocialLinks */
export const FloatingWhatsApp = FloatingSocialLinks;
