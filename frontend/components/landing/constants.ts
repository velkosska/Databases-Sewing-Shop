/** Costuras de Paqui — business copy and contact (from Google Business profile). */

export const BUSINESS_NAME = "Costuras de Paqui";

export const TAGLINE = "¡Dale una segunda oportunidad a tu ropa!";

export const HERO_SUBTITLE = "Arreglos, bordados y tintorería en Madrid";

export const CONTACT_NAME = "Paqui Espinosa";

export const PHONE_DISPLAY = "+34 693 92 91 36";
export const PHONE_HREF = "tel:+34693929136";

export const WHATSAPP_URL = "https://wa.me/34693929136";

export const EMAIL = "francales4@gmail.com";
export const EMAIL_HREF = "mailto:francales4@gmail.com";

export const ADDRESS = "San Enrique, 16, Puesto 2 y 4 exterior, Madrid";

export const WEBSITE_URL = "https://costuras-de-paqui.negocio.site";

export const INSTAGRAM_URL = "https://www.instagram.com/costurasdepaqui/";

export const TIKTOK_URL = "https://www.tiktok.com/@costuras_paqui1";

export const ABOUT_BIO =
  "Me dedico a arreglar y modificar ropa en múltiples tejidos — textil, pieles y más. También trabajo ropa de hogar (cojines, cortinas), ropa de motoristas, bordados y tintorería. En el Mercado Municipal de San Enrique te atiendo con trato cercano y presupuesto claro antes de empezar.";

export const OPENING_HOURS = [
  { days: "Lunes a viernes", times: "8:00 – 14:00 · 15:00 – 20:30" },
  { days: "Sábados", times: "8:00 – 14:00 · 16:00 – 19:00" },
] as const;

/** Matches shop/management/commands/seed_catalogue.py DEFAULT_CATALOGUE */
export const SERVICES = [
  {
    title: "Arreglos de ropa",
    description:
      "Arreglamos todo tipo de prendas en múltiples tejidos, incluida piel. Roturas, ajustes y transformaciones.",
  },
  {
    title: "Arreglo de prendas de motoristas",
    description: "Especialista en arreglo de equipamiento de motorista, incluida piel.",
  },
  {
    title: "Cambios de cremalleras",
    description: "Sustitución y reparación de cremalleras en pantalones, chaquetas y más.",
  },
  {
    title: "Bajos",
    description: "Bajos de pantalones y otras prendas, con acabado limpio y duradero.",
  },
  {
    title: "Reducción de tallas",
    description: "Ajuste y entallado de prendas para que te queden como deben.",
  },
  {
    title: "Modificación de ropa de hogar",
    description: "Customizamos y modificamos cojines, cortinas y más textiles del hogar.",
  },
  {
    title: "Bordados",
    description: "Bordados decorativos y personalizados para prendas y textiles.",
  },
  {
    title: "Tintorería",
    description: "Servicio de tintorería para que tus prendas queden impecables.",
  },
] as const;
