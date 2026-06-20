const path = require('path')

/** @type {import('vls').VeturConfig} */
module.exports = {
  settings: {
    'vetur.useWorkspaceDependencies': true,
    'vetur.experimental.templateInterpolationService': true,
  },
  projects: [
    {
      root: path.resolve(__dirname),
      tsconfig: path.resolve(__dirname, 'tsconfig.json'),
    },
  ],
}
