import type { Component } from 'vue';
import QcFunctionFlagPlateau from '@/components/QcFunctionFlagPlateau.vue';
import QcFunctionFlagIsolated from '@/components/QcFunctionFlagIsolated.vue';
import QcFunctionFlagJumps from '@/components/QcFunctionFlagJumps.vue';
import QcFunctionFlagOffset from '@/components/QcFunctionFlagOffset.vue';
import QcFunctionFlagRange from '@/components/QcFunctionFlagRange.vue';
import QcFunctionFlagAll from '@/components/QcFunctionFlagAll.vue';
import QcFunctionFlagUniLOF from '@/components/QcFunctionFlagUniLOF.vue';
import QcFunctionFlagZScore from '@/components/QcFunctionFlagZScore.vue';
import QcFunctionFlagByScatterLowpass from '@/components/QcFunctionFlagByScatterLowpass.vue';
import QcFunctionPropagateFlags from '@/components/QcFunctionPropagateFlags.vue';
import QcFunctionRenameField from '@/components/QcFunctionRenameField.vue';
import QcFunctionRolling from '@/components/QcFunctionRolling.vue';
import QcFunctionTransferFlags from '@/components/QcFunctionTransferFlags.vue';
import QcFunctionProcessGeneric from '@/components/QCFunctionProcessGeneric.vue';
import QCFunctionFlagGeneric from '@/components/QCFunctionFlagGeneric.vue';
import QcFunctionFlagConstants from '@/components/QcFunctionFlagConstants.vue';

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
  | 'processGeneric'
  | 'flagGeneric'
  | 'flagConstants';

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
  processGeneric: QcFunctionProcessGeneric,
  flagGeneric: QCFunctionFlagGeneric,
  flagConstants: QcFunctionFlagConstants,
};

export function getQcFunctionComponent(functionName: QcFunctionName): Component | null {
  return qcFunctionComponents[functionName] ?? null;
}
