#!/usr/bin/env node
/**
 * SRT Diff Preview Generator
 *
 * Usage:
 *   node generate_diff.js <original.srt> <candidate.srt> <output.html> [--corrections corrections.json]
 *   node generate_diff.js prepare-review <original.srt> [--candidate candidate.srt] [--output output.html] [--corrections corrections.json] [--force-candidate]
 *   node generate_diff.js review-plan <original.srt> [--size 100]
 *   node generate_diff.js review-chunks <original.srt> <candidate.srt> <output.json> [--size 100]
 *   node generate_diff.js apply-decisions <original.srt> <candidate.srt> <decisions.json> <output.srt> [--corrections corrections.json]
 *   node generate_diff.js update-corrections <new_corrections.json> --corrections corrections.json
 */

const fs = require('fs');
const path = require('path');

function parseSRT(content) {
  const subtitles = [];
  const blocks = content.replace(/\r\n/g, '\n').trim().split(/\n\s*\n/);

  for (const block of blocks) {
    const lines = block.trim().split('\n');
    if (lines.length < 3) continue;

    const id = parseInt(lines[0], 10);
    const timestamp = lines[1];
    const text = lines.slice(2).join('\n');

    subtitles.push({ id, timestamp, text });
  }

  return subtitles;
}

function serializeSRT(subtitles) {
  return subtitles.map((subtitle) => {
    return `${subtitle.id}\n${subtitle.timestamp}\n${subtitle.text}`;
  }).join('\n\n') + '\n';
}

function cloneSubtitle(subtitle) {
  return {
    id: subtitle.id,
    timestamp: subtitle.timestamp,
    text: subtitle.text,
  };
}

function applyCorrectionToText(text, correction) {
  if (!correction || !correction.from || correction.to === undefined) {
    return text;
  }

  if (correction.regex) {
    try {
      return text.replace(new RegExp(correction.from, 'gi'), correction.to);
    } catch (e) {
      return text;
    }
  }

  return text.split(correction.from).join(correction.to);
}

function applyCorrectionsToSubtitles(subtitles, corrections) {
  return subtitles.map((subtitle) => {
    let text = subtitle.text;

    for (const correction of corrections || []) {
      text = applyCorrectionToText(text, correction);
    }

    return {
      ...cloneSubtitle(subtitle),
      text,
    };
  });
}

function normalizeCorrection(correction) {
  return {
    from: correction.from,
    to: correction.to,
    reason: correction.reason || '',
    regex: Boolean(correction.regex),
  };
}

function extractManualCorrections(payload) {
  if (!payload) {
    return [];
  }

  const corrections = Array.isArray(payload)
    ? payload
    : (payload.corrections || payload.manualCorrections || []);

  return corrections
    .filter((correction) => correction && correction.from && correction.to)
    .map(normalizeCorrection);
}

function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function isAsciiWordChar(char) {
  return /^[A-Za-z0-9_]$/.test(char || '');
}

function createTextDiff(beforeText, afterText) {
  const beforeChars = Array.from(beforeText || '');
  const afterChars = Array.from(afterText || '');

  let prefixLength = 0;
  while (
    prefixLength < beforeChars.length &&
    prefixLength < afterChars.length &&
    beforeChars[prefixLength] === afterChars[prefixLength]
  ) {
    prefixLength += 1;
  }

  let suffixLength = 0;
  while (
    suffixLength < beforeChars.length - prefixLength &&
    suffixLength < afterChars.length - prefixLength &&
    beforeChars[beforeChars.length - 1 - suffixLength] === afterChars[afterChars.length - 1 - suffixLength]
  ) {
    suffixLength += 1;
  }

  while (
    suffixLength > 0 &&
    (
      isAsciiWordChar(beforeChars[beforeChars.length - suffixLength]) ||
      isAsciiWordChar(afterChars[afterChars.length - suffixLength])
    )
  ) {
    suffixLength -= 1;
  }

  while (
    prefixLength > 0 &&
    (
      isAsciiWordChar(beforeChars[prefixLength - 1]) ||
      isAsciiWordChar(afterChars[prefixLength - 1])
    ) &&
    (
      isAsciiWordChar(beforeChars[prefixLength]) ||
      isAsciiWordChar(afterChars[prefixLength])
    )
  ) {
    prefixLength -= 1;
  }

  const beforePrefix = beforeChars.slice(0, prefixLength).join('');
  const beforeChanged = beforeChars.slice(prefixLength, beforeChars.length - suffixLength).join('');
  const beforeSuffix = suffixLength > 0 ? beforeChars.slice(beforeChars.length - suffixLength).join('') : '';

  const afterPrefix = afterChars.slice(0, prefixLength).join('');
  const afterChanged = afterChars.slice(prefixLength, afterChars.length - suffixLength).join('');
  const afterSuffix = suffixLength > 0 ? afterChars.slice(afterChars.length - suffixLength).join('') : '';

  const beforeHtml = [
    escapeHtml(beforePrefix),
    beforeChanged ? `<span class="highlight-removed">${escapeHtml(beforeChanged)}</span>` : '',
    escapeHtml(beforeSuffix),
  ].join('');

  const afterHtml = [
    escapeHtml(afterPrefix),
    afterChanged ? `<span class="highlight-added">${escapeHtml(afterChanged)}</span>` : '',
    escapeHtml(afterSuffix),
  ].join('');

  return { beforeHtml, afterHtml };
}

function findDifferences(original, fixed, corrections) {
  const diffs = [];

  // Create lookup maps
  const originalMap = new Map(original.map(s => [s.id, s]));
  const fixedMap = new Map(fixed.map(s => [s.id, s]));

  // Find all IDs from both files
  const allIds = new Set([...originalMap.keys(), ...fixedMap.keys()]);

  for (const id of allIds) {
    const orig = originalMap.get(id);
    const fix = fixedMap.get(id);

    const origText = orig ? orig.text : '';
    const fixText = fix ? fix.text : '';
    const timestamp = orig ? orig.timestamp : (fix ? fix.timestamp : '');

    if (origText !== fixText) {
      const textDiff = createTextDiff(origText, fixText);
      // Determine if this matches a known correction
      let changeType = 'ai';
      let matchedCorrection = null;

      for (const corr of corrections) {
        if (corr.regex) {
          try {
            const regex = new RegExp(corr.from, 'gi');
            if (regex.test(origText)) {
              changeType = 'vocabulary';
              matchedCorrection = corr;
              break;
            }
          } catch (e) {
            // Invalid regex, skip
          }
        } else {
          if (origText.includes(corr.from)) {
            changeType = 'vocabulary';
            matchedCorrection = corr;
            break;
          }
        }
      }

      diffs.push({
        id,
        timestamp,
        before: origText,
        after: fixText,
        beforeHtml: textDiff.beforeHtml,
        afterHtml: textDiff.afterHtml,
        type: changeType,
        status: 'accepted',
        selected: true,
        reason: matchedCorrection ? matchedCorrection.reason : 'AI建议',
        sourceCorrection: matchedCorrection ? normalizeCorrection(matchedCorrection) : null,
      });
    }
  }

  return diffs.sort((a, b) => a.id - b.id);
}

function createReviewRows(original, fixed, diffs) {
  const diffMap = new Map(diffs.map((diff) => [diff.id, diff]));
  const fixedMap = new Map(fixed.map((subtitle) => [subtitle.id, subtitle]));
  let changeNumber = 0;

  return original.map((subtitle) => {
    const diff = diffMap.get(subtitle.id);

    if (diff) {
      changeNumber += 1;
      return {
        ...diff,
        kind: 'changed',
        changeNumber,
      };
    }

    const fixedSubtitle = fixedMap.get(subtitle.id);
    const text = fixedSubtitle ? fixedSubtitle.text : subtitle.text;
    return {
      id: subtitle.id,
      timestamp: subtitle.timestamp,
      before: subtitle.text,
      after: text,
      beforeHtml: escapeHtml(subtitle.text),
      afterHtml: escapeHtml(text),
      type: 'unchanged',
      status: 'unchanged',
      selected: false,
      reason: '',
      sourceCorrection: null,
      kind: 'unchanged',
      changeNumber: null,
    };
  });
}

function createReviewChunks(original, candidate, chunkSize = 100) {
  const candidateMap = new Map(candidate.map((subtitle) => [subtitle.id, subtitle]));
  const safeChunkSize = Math.max(1, Number.parseInt(chunkSize, 10) || 100);
  const chunks = [];

  for (let index = 0; index < original.length; index += safeChunkSize) {
    const subtitles = original.slice(index, index + safeChunkSize);
    const items = subtitles.map((subtitle) => {
      const candidateSubtitle = candidateMap.get(subtitle.id);
      const candidateText = candidateSubtitle ? candidateSubtitle.text : subtitle.text;

      return {
        id: subtitle.id,
        timestamp: subtitle.timestamp,
        originalText: subtitle.text,
        candidateText,
        changedByCandidate: subtitle.text !== candidateText,
      };
    });

    chunks.push({
      chunkNumber: chunks.length + 1,
      startId: items[0] ? items[0].id : null,
      endId: items[items.length - 1] ? items[items.length - 1].id : null,
      items,
    });
  }

  return chunks;
}

function createReviewChunkPlan(subtitles, chunkSize = 100) {
  const safeChunkSize = Math.max(1, Number.parseInt(chunkSize, 10) || 100);
  const ranges = [];

  for (let index = 0; index < subtitles.length; index += safeChunkSize) {
    const chunkSubtitles = subtitles.slice(index, index + safeChunkSize);

    ranges.push({
      chunkNumber: ranges.length + 1,
      startId: chunkSubtitles[0] ? chunkSubtitles[0].id : null,
      endId: chunkSubtitles[chunkSubtitles.length - 1] ? chunkSubtitles[chunkSubtitles.length - 1].id : null,
      itemCount: chunkSubtitles.length,
    });
  }

  return {
    subtitleCount: subtitles.length,
    chunkSize: safeChunkSize,
    chunkCount: ranges.length,
    ranges,
  };
}

function generateHTML(diffs, originalFile, fixedFile, subtitles = [], reviewRows = null) {
  const templatePath = path.join(__dirname, '../assets/diff_preview_template.html');
  let template = fs.readFileSync(templatePath, 'utf8');

  // Replace metadata
  template = template.replace('original.srt', escapeHtml(path.basename(originalFile)));
  template = template.replace('fixed.srt', escapeHtml(path.basename(fixedFile)));

  // Inject diff data
  const diffJSON = JSON.stringify(diffs, null, 2);
  template = template.replace(
    'let diffData = window.diffData || [];',
    `let diffData = ${diffJSON};`
  );

  const subtitleJSON = JSON.stringify(subtitles, null, 2);
  template = template.replace(
    'let subtitleData = window.subtitleData || [];',
    `let subtitleData = ${subtitleJSON};`
  );

  const reviewRowsJSON = JSON.stringify(reviewRows || createReviewRows(subtitles, subtitles, diffs), null, 2);
  template = template.replace(
    'let reviewRows = window.reviewRows || [];',
    `let reviewRows = ${reviewRowsJSON};`
  );

  const reviewMetaJSON = JSON.stringify({
    originalName: path.basename(originalFile),
    candidateName: path.basename(fixedFile),
  }, null, 2);
  template = template.replace(
    'let reviewMeta = window.reviewMeta || {};',
    `let reviewMeta = ${reviewMetaJSON};`
  );

  return template;
}

function applyReviewDecisions({ original, candidate, decisions }) {
  const candidateMap = new Map(candidate.map((subtitle) => [subtitle.id, subtitle]));
  const acceptedIds = new Set(decisions.acceptedChangeIds || []);
  const manualLineEdits = decisions.manualLineEdits || [];

  const outputMap = new Map(original.map((subtitle) => [subtitle.id, cloneSubtitle(subtitle)]));

  for (const id of acceptedIds) {
    const fixedSubtitle = candidateMap.get(id);
    const outputSubtitle = outputMap.get(id);

    if (fixedSubtitle && outputSubtitle) {
      outputSubtitle.text = fixedSubtitle.text;
    }
  }

  for (const edit of manualLineEdits) {
    const outputSubtitle = outputMap.get(edit.id);

    if (outputSubtitle) {
      outputSubtitle.text = edit.after;
    }
  }

  return {
    subtitles: Array.from(outputMap.values()).sort((a, b) => a.id - b.id),
    manualCorrections: decisions.manualCorrections || [],
  };
}

function loadCorrections(correctionsPath) {
  if (!correctionsPath || !fs.existsSync(correctionsPath)) {
    return [];
  }

  const corrData = JSON.parse(fs.readFileSync(correctionsPath, 'utf8'));
  return corrData.corrections || [];
}

function getDefaultReviewPaths(originalPath) {
  const dir = path.dirname(originalPath);
  const ext = path.extname(originalPath) || '.srt';
  const base = path.basename(originalPath, ext);

  return {
    candidatePath: path.join(dir, `${base}_candidate${ext}`),
    outputPath: path.join(dir, `${base}_diff_preview.html`),
  };
}

function prepareReviewFiles({ originalPath, candidatePath, outputPath, correctionsPath, forceCandidate = false }) {
  const corrections = loadCorrections(correctionsPath);
  const originalContent = fs.readFileSync(originalPath, 'utf8');
  const original = parseSRT(originalContent);

  const defaultPaths = getDefaultReviewPaths(originalPath);
  const resolvedCandidatePath = candidatePath || defaultPaths.candidatePath;
  const resolvedOutputPath = outputPath || defaultPaths.outputPath;

  let candidate;
  let candidateCreated = false;

  if (!forceCandidate && fs.existsSync(resolvedCandidatePath)) {
    candidate = parseSRT(fs.readFileSync(resolvedCandidatePath, 'utf8'));
  } else {
    candidate = applyCorrectionsToSubtitles(original, corrections);
    fs.writeFileSync(resolvedCandidatePath, serializeSRT(candidate), 'utf8');
    candidateCreated = true;
  }

  const diffs = findDifferences(original, candidate, corrections);
  const reviewRows = createReviewRows(original, candidate, diffs);
  const html = generateHTML(diffs, originalPath, resolvedCandidatePath, original, reviewRows);

  fs.writeFileSync(resolvedOutputPath, html, 'utf8');

  return {
    candidateCreated,
    candidatePath: resolvedCandidatePath,
    outputPath: resolvedOutputPath,
    diffs,
  };
}

function appendCorrections(correctionsPath, newCorrections) {
  if (!correctionsPath || newCorrections.length === 0) {
    return 0;
  }

  const existing = fs.existsSync(correctionsPath)
    ? JSON.parse(fs.readFileSync(correctionsPath, 'utf8'))
    : { corrections: [] };

  const corrections = existing.corrections || [];
  const seen = new Set(corrections.map((correction) => {
    return `${correction.from}\u0000${correction.to}\u0000${Boolean(correction.regex)}`;
  }));

  let added = 0;
  for (const correction of newCorrections.map(normalizeCorrection)) {
    const key = `${correction.from}\u0000${correction.to}\u0000${Boolean(correction.regex)}`;
    if (!seen.has(key)) {
      corrections.push(correction);
      seen.add(key);
      added += 1;
    }
  }

  fs.writeFileSync(correctionsPath, JSON.stringify({ corrections }, null, 2) + '\n', 'utf8');
  return added;
}

function getFlagValue(args, flagName) {
  const flagIndex = args.indexOf(flagName);
  if (flagIndex === -1) {
    return null;
  }

  return args[flagIndex + 1] || null;
}

function printUsage() {
  console.log('Usage: node generate_diff.js <original.srt> <candidate.srt> <output.html> [--corrections corrections.json]');
  console.log('       node generate_diff.js prepare-review <original.srt> [--candidate candidate.srt] [--output output.html] [--corrections corrections.json] [--force-candidate]');
  console.log('       node generate_diff.js review-plan <original.srt> [--size 100]');
  console.log('       node generate_diff.js review-chunks <original.srt> <candidate.srt> <output.json> [--size 100]');
  console.log('       node generate_diff.js apply-decisions <original.srt> <candidate.srt> <decisions.json> <output.srt> [--corrections corrections.json]');
  console.log('       node generate_diff.js update-corrections <new_corrections.json> --corrections corrections.json');
}

function printReviewSummary(result) {
  console.log(`Generated candidate SRT: ${result.candidatePath}`);
  if (!result.candidateCreated) {
    console.log('  - Reused existing candidate file');
  }
  console.log(`Generated diff preview: ${result.outputPath}`);
  console.log(`Found ${result.diffs.length} differences`);

  const vocabCount = result.diffs.filter(d => d.type === 'vocabulary').length;
  const aiCount = result.diffs.filter(d => d.type === 'ai').length;
  console.log(`  - Vocabulary corrections: ${vocabCount}`);
  console.log(`  - AI corrections: ${aiCount}`);
}

function prepareReviewCommand(args) {
  if (args.length < 2) {
    printUsage();
    process.exit(1);
  }

  const [, originalPath] = args;
  const candidatePath = getFlagValue(args, '--candidate');
  const outputPath = getFlagValue(args, '--output');
  const correctionsPath = getFlagValue(args, '--corrections');
  const forceCandidate = args.includes('--force-candidate');

  const result = prepareReviewFiles({
    originalPath,
    candidatePath,
    outputPath,
    correctionsPath,
    forceCandidate,
  });

  printReviewSummary(result);
}

function reviewChunksCommand(args) {
  if (args.length < 4) {
    printUsage();
    process.exit(1);
  }

  const [, originalPath, candidatePath, outputPath] = args;
  const chunkSize = getFlagValue(args, '--size') || 100;
  const original = parseSRT(fs.readFileSync(originalPath, 'utf8'));
  const candidate = parseSRT(fs.readFileSync(candidatePath, 'utf8'));
  const chunks = createReviewChunks(original, candidate, chunkSize);
  const payload = {
    version: 1,
    originalPath,
    candidatePath,
    chunkSize: Math.max(1, Number.parseInt(chunkSize, 10) || 100),
    subtitleCount: original.length,
    chunkCount: chunks.length,
    chunks,
  };

  fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2) + '\n', 'utf8');

  console.log(`Generated review chunks: ${outputPath}`);
  console.log(`Subtitle count: ${payload.subtitleCount}`);
  console.log(`Chunk count: ${payload.chunkCount}`);
}

function reviewPlanCommand(args) {
  if (args.length < 2) {
    printUsage();
    process.exit(1);
  }

  const [, originalPath] = args;
  const chunkSize = getFlagValue(args, '--size') || 100;
  const original = parseSRT(fs.readFileSync(originalPath, 'utf8'));
  const plan = createReviewChunkPlan(original, chunkSize);
  const ranges = plan.ranges
    .map((range) => `${range.startId}-${range.endId}`)
    .join(', ');

  console.log(`Review plan for: ${originalPath}`);
  console.log(`Subtitle count: ${plan.subtitleCount}`);
  console.log(`Chunk size: ${plan.chunkSize}`);
  console.log(`Chunk count: ${plan.chunkCount}`);
  console.log(`Chunk ranges: ${ranges}`);
}

function generatePreviewCommand(args) {
  if (args.length < 3) {
    printUsage();
    process.exit(1);
  }

  const [originalPath, fixedPath, outputPath] = args;
  const correctionsPath = getFlagValue(args, '--corrections');

  const result = prepareReviewFiles({
    originalPath,
    candidatePath: fixedPath,
    outputPath,
    correctionsPath,
  });

  printReviewSummary(result);
}

function applyDecisionsCommand(args) {
  if (args.length < 5) {
    printUsage();
    process.exit(1);
  }

  const [, originalPath, candidatePath, decisionsPath, outputPath] = args;
  const correctionsPath = getFlagValue(args, '--corrections');

  const original = parseSRT(fs.readFileSync(originalPath, 'utf8'));
  const candidate = parseSRT(fs.readFileSync(candidatePath, 'utf8'));
  const decisions = JSON.parse(fs.readFileSync(decisionsPath, 'utf8'));

  const result = applyReviewDecisions({ original, candidate, decisions });
  fs.writeFileSync(outputPath, serializeSRT(result.subtitles), 'utf8');

  const addedCorrections = appendCorrections(correctionsPath, result.manualCorrections);

  console.log(`Generated reviewed SRT: ${outputPath}`);
  console.log(`Applied accepted changes: ${(decisions.acceptedChangeIds || []).length}`);
  console.log(`Applied manual line edits: ${(decisions.manualLineEdits || []).length}`);
  if (correctionsPath) {
    console.log(`Added manual corrections: ${addedCorrections}`);
  }
}

function updateCorrectionsCommand(args) {
  if (args.length < 2) {
    printUsage();
    process.exit(1);
  }

  const [, payloadPath] = args;
  const correctionsPath = getFlagValue(args, '--corrections');

  if (!correctionsPath) {
    console.error('Missing required --corrections path');
    process.exit(1);
  }

  const payload = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
  const corrections = extractManualCorrections(payload);
  const addedCorrections = appendCorrections(correctionsPath, corrections);

  console.log(`Read manual corrections: ${corrections.length}`);
  console.log(`Added manual corrections: ${addedCorrections}`);
  console.log(`Updated corrections file: ${correctionsPath}`);
}

function main() {
  const args = process.argv.slice(2);

  if (args[0] === 'apply-decisions') {
    applyDecisionsCommand(args);
    return;
  }

  if (args[0] === 'update-corrections') {
    updateCorrectionsCommand(args);
    return;
  }

  if (args[0] === 'prepare-review') {
    prepareReviewCommand(args);
    return;
  }

  if (args[0] === 'review-plan') {
    reviewPlanCommand(args);
    return;
  }

  if (args[0] === 'review-chunks') {
    reviewChunksCommand(args);
    return;
  }

  generatePreviewCommand(args);
}

if (require.main === module) {
  main();
}

module.exports = {
  appendCorrections,
  applyCorrectionsToSubtitles,
  applyReviewDecisions,
  createReviewChunkPlan,
  createReviewChunks,
  createReviewRows,
  createTextDiff,
  extractManualCorrections,
  findDifferences,
  getDefaultReviewPaths,
  generateHTML,
  loadCorrections,
  parseSRT,
  prepareReviewFiles,
  serializeSRT,
};
