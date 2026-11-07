import { openTrackerPanel } from './helpers/tracker';
import { expect, test } from '@playwright/test';
import type { Page } from '@playwright/test';
import scenarioFixture from '../fixtures/scenario.json' with { type: 'json' };
import type { Scenario } from '@/entities/admission-scenario';
import type { ArchiveHistoryItem, SourceGroup } from '@/entities/admission-source';

const subscriptionId = 'sub-demo';
const template = scenarioFixture as Scenario;
const candidate = {
  rowRef: 'synthetic-row',
  officialRank: 3,
  score: '250',
  consent: false,
  priority: 1,
  participation: 'active' as const,
};

function group(revision = 1, seats: number | null = 2): SourceGroup {
  return {
    id: 'group-demo',
    universityId: 'uni-demo',
    universityName: 'Synthetic archive university',
    parentUniversityId: null,
    year: 2026,
    level: 'bachelor',
    title: 'Synthetic archive refresh',
    studyForm: 'full-time',
    funding: 'budget',
    category: 'general',
    seats,
    coverage: 'archive',
    dataKind: 'archive',
    sourceId: 'source-demo',
    sourceUrl: 'https://example.org/synthetic-archive',
    sourceState: 'archived',
    snapshotId: `snapshot-${revision}`,
    fetchedAt: `2026-11-0${revision}T00:00:00Z`,
    sourceUpdatedAt: null,
    lastCheckedAt: `2026-11-0${revision}T00:00:00Z`,
    rowCount: 20,
    lookupAvailable: true,
    scenarioAvailable: seats !== null && seats > 0,
    assessmentAvailable: false,
  };
}

function scenario(revision: number, sameSnapshot: boolean): Scenario {
  const currentGroup = group(sameSnapshot ? 1 : revision);
  return {
    ...template,
    id: `scenario-${revision}`,
    snapshotId: currentGroup.snapshotId,
    fetchedAt: currentGroup.fetchedAt,
    assessedAt: `2026-11-0${revision}T01:00:00Z`,
    previousId: revision === 1 ? null : 'scenario-1',
    explanation: {
      ...template.explanation!,
      summary: `Synthetic saved processing ${revision}`,
    },
  };
}

function historyItem(revision: number, sameSnapshot = false): ArchiveHistoryItem {
  return {
    id: `history-${revision}`,
    assessedAt: `2026-11-0${revision}T01:00:00Z`,
    modelVersion: 'source-facts-v1',
    group: {
      ...group(sameSnapshot ? 1 : revision),
      lookupAvailable: false,
      scenarioAvailable: false,
    },
    candidate,
    present: true,
  };
}

async function installArchive(page: Page, sameSnapshot = false) {
  const state = {
    revision: 1,
    historyUnavailable: false,
    historyItems: null as ArchiveHistoryItem[] | null,
    reads: {} as Record<string, number>,
  };
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1/', '');
    state.reads[path] = (state.reads[path] ?? 0) + 1;
    let value: unknown;
    if (path === 'session') {
      return route.request().method() === 'POST'
        ? route.fulfill({ status: 204 })
        : route.fulfill({
            json: { expiresAt: '2026-12-01T00:00:00Z', draftScope: 'a'.repeat(64) },
          });
    }
    if (path === 'watches') value = [];
    else if (path === 'direction-budget') {
      value = { limit: 20, total: 1, manualCount: 0, archiveCount: 1 };
    } else if (path === 'changes') {
      const latest = scenario(2, sameSnapshot);
      const items =
        state.revision === 1
          ? []
          : [
              {
                id: 'change-2',
                title: 'Synthetic saved change',
                createdAt: latest.assessedAt,
                seenAt: null,
                scenario: latest,
              },
            ];
      value = { items, total: items.length, unreadCount: items.length, nextCursor: null };
    } else if (path === 'subscriptions') {
      value = [
        {
          id: subscriptionId,
          createdAt: '2026-11-01T00:00:00Z',
          group: group(sameSnapshot ? 1 : state.revision),
          candidate,
          confirmedSnapshotId: 'snapshot-1',
          notice: null,
        },
      ];
    } else if (path.endsWith('/scenario')) value = scenario(state.revision, sameSnapshot);
    else if (path.endsWith('/scenario-history')) {
      const items =
        state.revision === 1
          ? [scenario(1, sameSnapshot)]
          : [scenario(2, sameSnapshot), scenario(1, sameSnapshot)];
      value = { items, total: items.length, nextCursor: null };
    } else if (path.includes('/scenarios/')) {
      const assessment = path.split('/').at(-1)!;
      value = {
        ...scenario(1, false),
        id: assessment,
        snapshotId: `snapshot-${assessment}`,
        previousId: assessment === 'immutable-new' ? 'immutable-old' : null,
        explanation: {
          ...template.explanation!,
          summary: `Immutable saved ${assessment}`,
        },
      };
    } else if (path.endsWith('/history')) {
      if (state.historyUnavailable) {
        return route.fulfill({ status: 503, json: { detail: 'Synthetic archive history outage' } });
      }
      const items =
        state.historyItems ??
        (state.revision === 1
          ? [historyItem(1, sameSnapshot)]
          : [historyItem(2, sameSnapshot), historyItem(1, sameSnapshot)]);
      value = { items, total: items.length, nextCursor: null };
    } else if (path === 'coverage') {
      value = {
        registeredSources: 0,
        reviewedSources: 0,
        importedSources: 0,
        importedGroups: 0,
        importedUniversities: 0,
        importedRows: 0,
        archiveImportedGroups: 0,
        conditionalGroups: 0,
        lastImportedAt: null,
        catalogUniversities: 1,
        automaticSources: 0,
        publishedGroups: 0,
        freshGroups: 0,
        archiveGroups: 0,
        nationalTotal: null,
        generatedAt: '2026-11-05T00:00:00Z',
      };
    } else {
      return route.fulfill({ status: 500, json: { detail: `Unexpected synthetic path: ${path}` } });
    }
    await route.fulfill({ json: value });
  });
  return state;
}

async function openHistories(page: Page) {
  await openTrackerPanel(page, 'archive');
  await openTrackerPanel(page, 'archive-facts');
  await openTrackerPanel(page, 'changes');
  await openTrackerPanel(page, 'archive-history');
  await page.getByRole('button', { name: 'История фактов', exact: true }).click();
  await openTrackerPanel(page, 'archive-history');
  await page.getByRole('button', { name: 'История условных сценариев', exact: true }).click();
  await expect(page.locator('.archive-fact-list > li')).toHaveCount(1);
  await expect(page.locator('.scenario-history > ol > li')).toHaveCount(1);
}

for (const sameSnapshot of [false, true]) {
  test(`explicit archive refresh updates mutable facts with ${sameSnapshot ? 'the same' : 'a new'} snapshot`, async ({
    page,
  }) => {
    const state = await installArchive(page, sameSnapshot);
    await page.goto('/tracker?direction=sub-demo&assessment=immutable-new');
    await openHistories(page);
    const comparison = page.getByRole('region', { name: 'Сравнение сохранённых сценариев' });
    await expect(comparison).toContainText('Immutable saved immutable-old');
    const immutableText = await comparison.innerText();

    state.revision = 2;
    const refresh = page.getByRole('button', { name: 'Перечитать сохранённые факты', exact: true });
    await refresh.click();
    await expect(refresh).toBeEnabled();
    await expect(page.locator('.source-provenance')).toContainText(
      sameSnapshot ? 'snapshot-1' : 'snapshot-2',
    );
    await expect(page.locator('.archive-fact-list > li')).toHaveCount(2);
    await expect(page.locator('.scenario-history > ol > li')).toHaveCount(2);
    await expect(page.locator('.scenario-summary')).toHaveText('Synthetic saved processing 2');
    await expect(page.getByRole('region', { name: 'Изменения в ваших списках' })).toContainText(
      'Synthetic saved change',
    );
    expect(state.reads['subscriptions/sub-demo/history']).toBeGreaterThanOrEqual(2);
    expect(state.reads.changes).toBeGreaterThanOrEqual(2);
    expect(state.reads['subscriptions/sub-demo/scenarios/immutable-new']).toBe(1);
    expect(state.reads['subscriptions/sub-demo/scenarios/immutable-old']).toBe(1);
    expect(await comparison.innerText()).toBe(immutableText);
  });
}

test('explicit refresh marks closed cached histories stale until they are opened again', async ({
  page,
}) => {
  const state = await installArchive(page, true);
  await page.goto('/tracker');
  await openHistories(page);
  await openTrackerPanel(page, 'archive-history');
  await page.getByRole('button', { name: 'История фактов', exact: true }).click();
  await openTrackerPanel(page, 'archive-history');
  await page.getByRole('button', { name: 'История условных сценариев', exact: true }).click();

  state.revision = 2;
  const refresh = page.getByRole('button', { name: 'Перечитать сохранённые факты', exact: true });
  await refresh.click();
  await expect(refresh).toBeEnabled();
  expect(state.reads['subscriptions/sub-demo/history']).toBe(1);
  expect(state.reads['subscriptions/sub-demo/scenario-history']).toBe(1);
  await openTrackerPanel(page, 'archive-history');
  await page.getByRole('button', { name: 'История фактов', exact: true }).click();
  await openTrackerPanel(page, 'archive-history');
  await page.getByRole('button', { name: 'История условных сценариев', exact: true }).click();
  await expect(page.locator('.archive-fact-list > li')).toHaveCount(2);
  await expect(page.locator('.scenario-history > ol > li')).toHaveCount(2);
});

test('failed refresh labels retained dated history and an explicit retry can recover', async ({
  page,
}) => {
  const state = await installArchive(page);
  await page.goto('/tracker');
  await openHistories(page);
  state.revision = 2;
  state.historyUnavailable = true;
  let releaseScenarioHistory!: () => void;
  const scenarioHistoryGate = new Promise<void>((resolve) => {
    releaseScenarioHistory = resolve;
  });
  await page.route('**/api/v1/subscriptions/sub-demo/scenario-history?*', async (route) => {
    await scenarioHistoryGate;
    await route.fallback();
  });

  const refresh = page.getByRole('button', { name: 'Перечитать сохранённые факты', exact: true });
  try {
    await refresh.click();
    await expect(page.locator('.archive-history [role="alert"]')).toContainText(
      'ранее загруженные датированные записи',
    );
    await expect(refresh).toBeDisabled();
  } finally {
    releaseScenarioHistory();
  }
  await expect(
    page.getByText('Не удалось перечитать все сохранённые факты.', { exact: false }),
  ).toBeVisible();
  await expect(refresh).toBeEnabled();
  await expect(page.locator('.archive-history [role="alert"]')).toContainText(
    'ранее загруженные датированные записи',
  );
  await expect(page.locator('.archive-fact-list > li')).toHaveCount(1);
  await expect(page.locator('.archive-fact-list')).toContainText('2026-11-01T00:00:00Z');
  await expect(page.locator('.scenario-summary')).toHaveText('Synthetic saved processing 2');
  await expect(page.locator('.source-provenance')).toContainText('snapshot-2');

  state.historyUnavailable = false;
  await refresh.click();
  await expect(refresh).toBeEnabled();
  await expect(page.locator('.archive-fact-list > li')).toHaveCount(2);
  await expect(page.locator('.archive-directions [role="alert"]')).toHaveCount(0);
});

const capacityCases = [
  {
    name: 'candidate disappears',
    beforePresent: true,
    afterPresent: false,
    beforeSeats: 2,
    afterSeats: 5,
    expected: 'Мест в группе: 2 → 5',
  },
  {
    name: 'candidate appears and capacity becomes known',
    beforePresent: false,
    afterPresent: true,
    beforeSeats: null,
    afterSeats: 5,
    expected: 'Мест в группе: неизвестно → 5',
  },
  {
    name: 'candidate stays absent and capacity becomes unknown',
    beforePresent: false,
    afterPresent: false,
    beforeSeats: 5,
    afterSeats: null,
    expected: 'Мест в группе: 5 → неизвестно',
  },
  {
    name: 'candidate disappears with unchanged capacity',
    beforePresent: true,
    afterPresent: false,
    beforeSeats: 2,
    afterSeats: 2,
    expected: null,
  },
  {
    name: 'candidate remains present with candidate fact changes',
    beforePresent: true,
    afterPresent: true,
    beforeSeats: 2,
    afterSeats: 5,
    expected: 'Мест в группе: 2 → 5',
  },
];

for (const item of capacityCases) {
  test(`archive capacity comparison when ${item.name}`, async ({ page }) => {
    const state = await installArchive(page);
    const before = historyItem(1);
    const after = historyItem(2);
    state.revision = 2;
    state.historyItems = [
      {
        ...after,
        group: { ...after.group, seats: item.afterSeats },
        candidate: item.afterPresent ? { ...candidate, consent: true } : null,
        present: item.afterPresent,
      },
      {
        ...before,
        group: { ...before.group, seats: item.beforeSeats },
        candidate: item.beforePresent ? candidate : null,
        present: item.beforePresent,
      },
    ];
    await page.goto('/tracker');
    await openTrackerPanel(page, 'archive-history');
    await page.getByRole('button', { name: 'История фактов', exact: true }).click();
    const comparison = page.getByRole('region', { name: 'Сравнение архивных фактов' });
    if (item.expected) {
      await expect(comparison).toContainText(item.expected);
    } else {
      await expect(comparison.getByText(/^Мест в группе:/)).toHaveCount(0);
    }
    if (item.beforePresent && item.afterPresent) {
      await expect(comparison).toContainText('Согласие: нет → да');
    } else {
      await expect(comparison).toContainText('Отсутствие не доказывает отзыв или отказ');
      await expect(comparison.getByText(/^Согласие:/)).toHaveCount(0);
    }
  });
}
