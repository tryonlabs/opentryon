import React from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './styles.module.css';

const surfaces = [
  {
    title: 'CLI',
    body: 'Run any registry model from the shell with one consistent flag set and --dry-run.',
    code: 'opentryon vton --model fashn-vton-1.5',
    to: '/getting-started/cli',
  },
  {
    title: 'MCP server',
    body: 'Every registry model is exposed as a tool for Claude, Cursor and other MCP clients.',
    code: 'python mcp-server/server.py',
    to: '/getting-started/mcp',
  },
  {
    title: 'TryOn Studio',
    body: 'An agent chat and capability screens that talk to the MCP server over HTTP.',
    code: 'Studio → MCP → models',
    to: '/getting-started/tryon-studio',
  },
  {
    title: 'Python APIs',
    body: 'Adapters under tryon.api and a single invoke_model() entry point.',
    code: 'from tryon.cli.runner import invoke_model',
    to: '/getting-started/quickstart',
  },
];

const stats = [
  {value: '148', label: 'models'},
  {value: '10', label: 'services'},
  {value: '4', label: 'ways to run'},
];

export default function HomeHero(): JSX.Element {
  // The hero is always navy, so it always uses the ivory-front mark
  const mark = useBaseUrl('/img/brand/opentryon-mark-dark.svg');

  return (
    <section className={styles.home}>
      <div className={styles.hero}>
        <div className={styles.copy}>
          <p className={styles.eyebrow}>Open source · v0.0.7</p>
          <p className={styles.title}>
            Open-source AI for fashion and virtual&nbsp;try-on.
          </p>
          <p className={styles.lead}>
            One model registry, four ways to run it. Drive 148 models across
            10 services from the CLI, an MCP server, TryOn Studio or Python.
          </p>
          <div className={styles.actions}>
            <Link className="button button--primary button--lg" to="/getting-started/installation">
              Get started
            </Link>
            <Link className={`button button--lg ${styles.ghost}`} to="/api-reference/overview">
              API reference
            </Link>
          </div>
        </div>

        <div className={styles.emblem} aria-hidden="true">
          <img className={styles.markImage} src={mark} alt="" />
        </div>
      </div>

      <dl className={styles.stats}>
        {stats.map((s) => (
          <div key={s.label} className={styles.stat}>
            <dt className={styles.statLabel}>{s.label}</dt>
            <dd className={styles.statValue}>{s.value}</dd>
          </div>
        ))}
      </dl>

      <div className={styles.surfaces}>
        {surfaces.map((s) => (
          <Link key={s.title} to={s.to} className={styles.card}>
            <h3 className={styles.cardTitle}>{s.title}</h3>
            <p className={styles.cardBody}>{s.body}</p>
            <code className={styles.cardCode}>{s.code}</code>
            <span className={styles.cardArrow} aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
