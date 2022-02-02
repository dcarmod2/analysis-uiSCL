import {Button} from '@chakra-ui/core'

export default function ListGroupItem({children, ...p}) {
  return (
    <Button
      isFullWidth
      borderRadius='4px'
      borderColor='#E2E8F0'
      justifyContent='left'
      height='unset'
      py={4}
      textAlign='left'
      whiteSpace='break-spaces'
      variant='outline'
      variantColor='blue'
      _notLast={{
        borderBottomLeftRadius: 0,
        borderBottomRightRadius: 0,
        borderBottom: 0
      }}
      _notFirst={{
        borderTopLeftRadius: 0,
        borderTopRightRadius: 0
      }}
      {...p}
    >
      {children}
    </Button>
  )
}
