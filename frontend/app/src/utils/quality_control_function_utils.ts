import type { Component } from 'vue';
import QcFunctionFlagPlateau from 'src/components/QcFunctionFlagPlateau.vue';
import QcFunctionFlagIsolated from 'src/components/QcFunctionFlagIsolated.vue';
import QcFunctionFlagJumps from 'src/components/QcFunctionFlagJumps.vue';
import QcFunctionFlagOffset from 'src/components/QcFunctionFlagOffset.vue';
import QcFunctionFlagRange from 'src/components/QcFunctionFlagRange.vue';
import QcFunctionFlagAll from 'src/components/QcFunctionFlagAll.vue';
import QcFunctionFlagUniLOF from 'src/components/QcFunctionFlagUniLOF.vue';
import QcFunctionFlagZScore from 'src/components/QcFunctionFlagZScore.vue';
import QcFunctionFlagByScatterLowpass from 'src/components/QcFunctionFlagByScatterLowpass.vue';
import QcFunctionPropagateFlags from 'src/components/QcFunctionPropagateFlags.vue';
import QcFunctionRenameField from 'src/components/QcFunctionRenameField.vue';
import QcFunctionRolling from 'src/components/QcFunctionRolling.vue';
import QcFunctionTransferFlags from 'src/components/QcFunctionTransferFlags.vue';

export type QcFunctionName =
  | 'flagPlateau'
  | 'flagIsolated'
  | 'flagJumps'
  | 'flagOffset'
  | 'flagRange'
  | 'flagAll'
  | 'flagUniLOF'
  | 'flagZScore'
  | 'flagByScatterLowpass'
  | 'propagateFlags'
  | 'renameField'
  | 'rolling'
  | 'transferFlags'

export const qcFunctionComponents: Record<QcFunctionName, Component> = {
  flagPlateau: QcFunctionFlagPlateau,
  flagIsolated: QcFunctionFlagIsolated,
  flagJumps: QcFunctionFlagJumps,
  flagOffset: QcFunctionFlagOffset,
  flagRange: QcFunctionFlagRange,
  flagAll: QcFunctionFlagAll,
  flagUniLOF: QcFunctionFlagUniLOF,
  flagZScore: QcFunctionFlagZScore,
  flagByScatterLowpass: QcFunctionFlagByScatterLowpass,
  propagateFlags: QcFunctionPropagateFlags,
  renameField: QcFunctionRenameField,
  rolling: QcFunctionRolling,
  transferFlags: QcFunctionTransferFlags,
};

export function getQcFunctionComponent(functionName: QcFunctionName): Component | null {
  return qcFunctionComponents[functionName] ?? null;
}
