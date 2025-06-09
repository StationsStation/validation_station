import { vi, expect, test } from 'vitest'
import { render } from '@testing-library/svelte'
import Hello from '../lib/components/AgentDeployer.svelte'

vi.mock('../../stores/configs', () => {
  return {
    configStore: {
      subscribe: (/** @type {(arg0: { exampleConfig: {}; }) => void} */ fn) => {
        fn({
          exampleConfig: {
            /* fill in some mock StrategyVars if needed */
          }
        })
        return () => {}
      }
    }
  }
})


test('New Agent Button message', () => {
    const { getAllByRole } = render(Hello)
    const buttons = getAllByRole('button', { name: /New Agent/i })
    expect(buttons.length).toBeGreaterThan(0)
})

