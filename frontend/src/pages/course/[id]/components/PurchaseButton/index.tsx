import { Text } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import { PurchaseModal } from 'components';
import Icon, { IconType } from 'components/Icon';
import Popover from 'components/Popover';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { Landing } from 'resources/landing/landing.types';

type PurchaseButtonProps = {
  landing: Pick<Landing, 'old_price' | 'price' | 'course'>;
};

const PurchaseButton = ({ landing }: PurchaseButtonProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <Popover
      position="top-start"
      buttonProps={{
        variant: 'filled',
        justify: 'space-between',
        rightSection: <Icon type={IconType.CircleArrow} color="inherit" />,
        miw: isMobile ? 200 : 400,
        w: isMobile ? 200 : 400,
        px: 20,
      }}
      target={
        <Text size="lg" inline>
          Buy for ${landing.price}{' '}
          <Text c="main.3" component="span" td="line-through">
            ${landing.old_price}
          </Text>
        </Text>
      }
    >
      <PurchaseModal course={landing.course} />
    </Popover>
  );
};

export default PurchaseButton;
