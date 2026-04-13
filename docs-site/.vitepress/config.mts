import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'cs-CZ',
  title: 'Metricord Docs',
  description: 'Dokumentace pro analytický systém Metricord',
  
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600&display=swap' }]
  ],

  themeConfig: {
    nav: [
      { text: 'Domů', link: '/' },
      { text: 'Dokumentace', link: '/introduction' },
      { text: 'Rychlý start', link: '/quickstart' },
      { text: 'GitHub', link: 'https://github.com/MarciPhan/2026-BP-Marcuska-PredikceChov-n-' }
    ],

    sidebar: [
      {
        text: 'Začínáme',
        items: [
          { text: 'Úvod', link: '/introduction' },
          { text: 'Vize & Cíle', link: '/vision' },
          { text: 'Whitepaper', link: '/whitepaper' },
          { text: 'Matematické základy', link: '/math-foundations' },
          { text: 'Rychlý start', link: '/quickstart' },
          { text: 'Uživatelská příručka', link: '/user-guide' },
          { text: 'Instalace', link: '/setup' },
          { text: 'Architektura', link: '/architecture' },
          { text: 'API Reference', link: '/api' },
          { text: 'Nasazení', link: '/deployment' },
          { text: 'Cloud Deployment', link: '/cloud-deployment' }
        ]
      },
      {
        text: 'Funkce bota',
        items: [
          { text: 'Slash příkazy', link: '/commands' },
          { text: 'Skóre bezpečnosti', link: '/security' },
          { text: 'Analytické metriky', link: '/analytics' },
          { text: 'Případové studie', link: '/case-studies' },
          { text: 'Export dat', link: '/export' },
          { text: 'Health Dashboard', link: '/health-dashboard' },
          { text: 'API Akce', link: '/api-actions' },
          { text: 'API Příklady', link: '/api-examples' }
        ]
      },
      {
        text: 'Pokročilé',
        items: [
          { text: 'Predikce & AI', link: '/ai' },
          { text: 'ML Modely', link: '/predictions' },
          { text: 'Smart Insights', link: '/insights' },
          { text: 'Integrace & Webhooky', link: '/integrations' },
          { text: 'Developer Guide', link: '/dev-guide' },
          { text: 'Data Science', link: '/data-science' },
          { text: 'Redis Schéma', link: '/data-schema' },
          { text: 'Škálování', link: '/scaling-global' },
          { text: 'Zabezpečení (Tech)', link: '/security-technical' },
          { text: 'OS Hardening', link: '/hardening' },
          { text: 'Labs (Experimenty)', link: '/labs' },
          { text: 'Admin Guide', link: '/admin-guide' },
          { text: 'ML Srovnání', link: '/ml-comparison' }
        ]
      },
      {
        text: 'Komunita',
        items: [
          { text: 'Moderátoři', link: '/moderators' },
          { text: 'Best Practices', link: '/best-practices' },
          { text: 'Role a XP', link: '/roles' },
          { text: 'Privacy Builder', link: '/privacy-builder' },
          { text: 'Vizuální styl', link: '/branding' },
          { text: 'Style Guide', link: '/style-guide' },
          { text: 'Konkurence', link: '/comparison' }
        ]
      },
      {
        text: 'O projektu',
        items: [
          { text: 'Roadmapa', link: '/changelog' },
          { text: 'Slovník pojmů', link: '/glossary' },
          { text: 'Časté dotazy', link: '/faq' },
          { text: 'Troubleshooting', link: '/troubleshooting' },
          { text: 'Podpora', link: '/support' }
        ]
      },
      {
        text: 'Právní informace',
        items: [
          { text: 'Ochrana dat', link: '/privacy' },
          { text: 'Podmínky služby', link: '/terms' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'discord', link: 'https://discord.gg/metricord' }
    ],

    search: {
      provider: 'local'
    }
  }
})
