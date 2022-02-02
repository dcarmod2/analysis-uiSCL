import {
  Alert,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack
} from '@chakra-ui/core'
import get from 'lodash/fp/get'
import {useRouter} from 'next/router'
import {useCallback, useState} from 'react'
import {useDispatch, useSelector} from 'react-redux'

import {deleteBundle, saveBundle} from 'lib/actions'
import useInput from 'lib/hooks/use-controlled-input'
import message from 'lib/message'
import {routeTo} from 'lib/router'

import ConfirmButton from './confirm-button'
import Select from './select'

const getOptionLabel = (b) =>
  `${b.name}${b.status === 'DONE' ? '' : `: ${b.status}`}`

const hasContent = (s) => s.length > 0

function FeedNameInput({feed, index, onChange, ...p}) {
  const input = useInput({onChange, test: hasContent, value: feed.name})
  return (
    <FormControl {...p} isInvalid={input.isInvalid}>
      <FormLabel htmlFor={input.id}>
        {`${message('bundle.feed')} #${index + 1}`}
      </FormLabel>
      <Input {...input} placeholder='Feed name' />
    </FormControl>
  )
}

function BundleNameInput({name, onChange, ...p}) {
  const input = useInput({onChange, test: hasContent, value: name})
  return (
    <FormControl {...p} isInvalid={input.isInvalid}>
      <FormLabel htmlFor={input.id}>{message('bundle.name')}</FormLabel>
      <Input {...input} placeholder='Network bundle name' />
    </FormControl>
  )
}

/**
 * Edit bundle is keyed by the bundle ID and will be completely unmounted and
 * recreated when that changes.
 */
export default function EditBundle(p) {
  const dispatch = useDispatch()
  const router = useRouter()
  const bundles = useSelector(get('region.bundles'))

  const {regionId} = router.query
  const [bundleId, setBundleId] = useState(router.query.bundleId)
  const originalBundle = bundles.find((b) => b._id === bundleId)
  const [bundle, setBundle] = useState(originalBundle)

  const setName = useCallback(
    (name) => setBundle((bundle) => ({...bundle, name})),
    [setBundle]
  )

  // If this bundle has project's associated with it. Disable deletion.
  const disableDelete = p.bundleProjects.length > 0

  async function _deleteBundle() {
    const {as, href} = routeTo('bundles', {regionId})
    router.push(href, as)
    dispatch(deleteBundle(bundleId))
  }

  async function _saveBundle() {
    const b = await dispatch(saveBundle(bundle))
    setBundle(b) // nonce update
  }

  function selectBundle(result) {
    setBundleId(result._id)
    const {as, href} = routeTo('bundleEdit', {regionId, bundleId: result._id})
    router.push(href, as)
  }

  function setFeedName(feedId, name) {
    if (bundle) {
      setBundle({
        ...bundle,
        feeds: bundle.feeds.map((f) => {
          if (f.feedId === feedId) {
            return {...f, name}
          }
          return f
        })
      })
    }
  }

  return (
    <Stack spacing={8}>
      <FormControl>
        <FormLabel htmlFor='selectBundle'>{message('bundle.select')}</FormLabel>
        <div>
          <Select
            inputId='selectBundle'
            options={bundles}
            getOptionLabel={getOptionLabel}
            getOptionValue={get('_id')}
            onChange={selectBundle}
            value={bundles.find((b) => b._id === bundleId)}
          />
        </div>
      </FormControl>

      {bundle && bundleId === router.query.bundleId && (
        <Stack spacing={4}>
          <Heading size='md'>{message('bundle.edit')}</Heading>

          {bundle.status === 'PROCESSING_GTFS' && (
            <Alert status='info'>{message('bundle.processing')}</Alert>
          )}

          {bundle.status === 'ERROR' && (
            <Alert status='error'>
              {message('bundle.failure')}
              <br />
              {bundle.statusText}
            </Alert>
          )}

          <BundleNameInput name={bundle.name} onChange={setName} />

          {bundle.feeds &&
            bundle.feeds.map((feed, index) => (
              <FeedNameInput
                feed={feed}
                index={index}
                key={feed.feedId}
                onChange={(name) => setFeedName(feed.feedId, name)}
              />
            ))}

          <Button
            isDisabled={bundle === originalBundle}
            onClick={_saveBundle}
            size='lg'
            title={message('bundle.save')}
            variantColor='yellow'
          >
            {message('bundle.save')}
          </Button>

          {disableDelete ? (
            <Alert status='info'>
              {message('bundle.deleteDisabled', {
                projects: p.bundleProjects.length
              })}
            </Alert>
          ) : (
            <ConfirmButton
              description={message('bundle.deleteConfirmation')}
              leftIcon='delete'
              onConfirm={_deleteBundle}
              size='lg'
              variantColor='red'
            >
              {message('bundle.delete')}
            </ConfirmButton>
          )}
        </Stack>
      )}
    </Stack>
  )
}
