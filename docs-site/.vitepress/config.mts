import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  lang: 'cs-CZ',
  title: 'Metricord Docs',
  description: 'Dokumentace pro analytický systém Metricord',
  base: '/2026-BP-Marcinka-PredikceChov-n-/',
  appearance: 'force-dark',
  ignoreDeadLinks: [
    /^http:\/\/localhost/
  ],
  
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600&display=swap' }],
    ['link', { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css' }]
  ],

  markdown: {
    math: true
  },

  themeConfig: {
    nav: [
      { text: 'Domů', link: '/' },
      { text: 'Vývoj', link: '/dev-guide' },
      { text: 'Rychlý start', link: '/quickstart' },
      { text: 'GitHub', link: 'https://github.com/MarciPhan/2026-BP-Marcuska-PredikceChov-n-' }
    ],

    sidebar: [
      {
        text: 'Začínáme',
        collapsed: false,
        items: [
          { text: 'Úvod', link: '/introduction' },
          { text: 'Rychlý start', link: '/quickstart' },
          { text: 'Instalace a konfigurace', link: '/setup' },
          { text: 'Architektura systému', link: '/architecture' }
        ]
      },
      {
        text: 'Uživatelská příručka',
        collapsed: false,
        items: [
          { text: 'Základní použití', link: '/user-guide' },
          { text: 'Příkazy bota', link: '/commands' },
          { text: 'XP systém a role', link: '/roles' },
          { text: 'Analytické metriky', link: '/analytics' },
          { text: 'Export dat', link: '/export' },
          { text: 'Backfill historických dat', link: '/backfill' },
          { text: 'Ochrana osobních údajů', link: '/privacy' }
        ]
      },
      {
        text: 'Příručka pro moderátory',
        collapsed: false,
        items: [
          { text: 'Průvodce pro moderátory', link: '/moderators' },
          { text: 'Osvědčené postupy', link: '/best-practices' },
          { text: 'Případové studie', link: '/case-studies' },
          { text: 'Smart Insights', link: '/insights' },
          { text: 'Skóre bezpečnosti', link: '/security' }
        ]
      },
      {
        text: 'Administrátorská příručka',
        collapsed: false,
        items: [
          { text: 'Nasazení do produkce', link: '/deployment' },
          { text: 'Správa instance', link: '/admin-guide' },
          { text: 'Monitoring systému', link: '/health-dashboard' },
          { text: 'Škálování a HA', link: '/scaling-global' },
          { text: 'Zabezpečení infrastruktury', link: '/hardening' },
          { text: 'Technické zabezpečení', link: '/security-technical' },
          { text: 'Privacy Builder', link: '/privacy-builder' },
          { text: 'Cloud Deployment', link: '/cloud-deployment' }
        ]
      },
      {
        text: 'Vývojářská příručka',
        collapsed: false,
        items: [
          { text: 'Lokální vývoj', link: '/dev-guide' },
          { text: 'API Reference', link: '/api' },
          { text: 'API akce', link: '/api-actions' },
          { text: 'API příklady', link: '/api-examples' },
          { text: 'Redis datové schéma', link: '/data-schema' },
          { text: 'Integrace a Webhooky', link: '/integrations' },
          { text: 'Data Science', link: '/data-science' },
          { text: 'Experimentální funkce', link: '/labs' },
          { text: 'Přehled predikce', link: '/ai' },
          { text: 'ML pipeline', link: '/predictions' },
          { text: 'Matematické základy', link: '/math-foundations' },
          { text: 'Srovnání ML algoritmů', link: '/ml-comparison' }
        ]
      },
      {
        text: 'Reference',
        collapsed: false,
        items: [
          { text: 'Slovník pojmů', link: '/glossary' },
          { text: 'Časté dotazy', link: '/faq' },
          { text: 'Řešení potíží', link: '/troubleshooting' },
          { text: 'Podmínky služby', link: '/terms' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'discord', link: 'https://discord.gg/metricord' }
    ],

    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: 'Hledat',
            buttonAriaLabel: 'Hledat'
          },
          modal: {
            displayDetails: 'Zobrazit podrobnosti',
            resetButtonTitle: 'Vymazat vyhledávání',
            backButtonTitle: 'Zavřít vyhledávání',
            noResultsText: 'Žádné výsledky pro',
            footer: {
              selectText: 'vybrat',
              navigateText: 'navigovat',
              closeText: 'zavřít'
            }
          }
        }
      }
    },
    
    docFooter: {
      prev: 'Předchozí strana',
      next: 'Další strana'
    },
    
    outline: {
      label: 'Na této stránce',
      level: [2, 3]
    },
    
    lastUpdated: {
      text: 'Naposledy aktualizováno',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short'
      }
    },
    
    langMenuLabel: 'Jazyk',
    returnToTopLabel: 'Zpět nahoru',
    sidebarMenuLabel: 'Menu'
  }
}))
