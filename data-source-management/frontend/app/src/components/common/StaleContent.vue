<script lang="ts">
/**
 * Fades out its content to indicate that it is outdated, e.g. a result whose input has changed since.
 *
 * Renders no element of its own: the style is applied directly to each child, so the children
 * keep their place in the surrounding layout (e.g. as flex items).
 */
import { cloneVNode, Comment, defineComponent } from 'vue';

export default defineComponent({
  name: 'StaleContent',
  props: {
    stale: { type: Boolean, default: false },
  },
  setup(props, { slots }) {
    return () =>
      (slots.default?.() ?? []).map((vnode) =>
        // keep reactivity
        vnode.type === Comment
          ? vnode
          : cloneVNode(vnode, { style: { opacity: props.stale ? 0.4 : undefined } }),
      );
  },
});
</script>
